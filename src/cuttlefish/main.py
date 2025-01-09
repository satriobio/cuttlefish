import argparse
import os
from minknow_api.manager import Manager
from minknow_api.tools.protocols import CriteriaValues

os.environ["MINKNOW_TRUSTED_CA"] = "/opt/ont/minknow/conf/rpc-certs/ca.crt"


def list_positions():
    manager = Manager()
    positions = list(manager.flow_cell_positions())
    for i, position in enumerate(positions):
        print(f"{i}: {position.name}")


def run_until(position_index, runtime=None, pores=None, action="pause", clear=False):
    if clear:
        runtime, pores, action = None, None, "pause"
        
    if runtime is None and pores is None and clear is False:
        print("Error: At least one of --runtime or --pores must be provided (unless --clear is specified).")
        return

    manager = Manager()
    positions = list(manager.flow_cell_positions())

    try:
        selected_position = positions[position_index]
    except IndexError:
        print("Invalid position index. Use 'cuttlefish list' to see available positions.")
        return

    device = selected_position.name
    criteria_args = {}

    if runtime is not None and runtime > 0:
        criteria_args['runtime'] = runtime

    if pores is not None and pores > 0:
        if device.startswith(('M', 'X')):
            calc = pores / 2048
        elif device.startswith('P') or isinstance(device, (int, float)):
            calc = pores / 12000
        else:
            print("Error: Unknown device type.")
            return
        criteria_args['available_pores'] = calc

    criteria = CriteriaValues(**criteria_args)
    target_criteria = {}

    if action.lower() == "pause":
        target_criteria['pause_criteria'] = criteria.as_protobuf()
    elif action.lower() == "stop":
        target_criteria['stop_criteria'] = criteria.as_protobuf()
    else:
        print("Error: Invalid action. Use 'pause' or 'stop'.")
        return

    connection = selected_position.connect()
    run = connection.protocol.get_current_protocol_run()
    acquisition_run_id = run.acquisition_run_ids[-1]

    try:
        connection.run_until.write_target_criteria(acquisition_run_id=acquisition_run_id, **target_criteria)
        print("Protocol updated")
        connection.protocol.resume_protocol()
        print("Protocol resumed")
    except Exception as e:
        print(e)
        print("Is the run still ongoing?")


def main():
    parser = argparse.ArgumentParser(prog="cuttlefish", description="Control nanopore devices with MinKNOW API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List available flow cell positions")

    # RunUntil command
    rununtil_parser = subparsers.add_parser("rununtil", help="Set RunUntil criteria")
    rununtil_parser.add_argument("--position", type=int, required=True, help="Index of the flow cell position")
    rununtil_parser.add_argument("--runtime", type=int, help="Runtime in seconds")
    rununtil_parser.add_argument("--pores", type=float, help="Available pores threshold (percentage)")
    rununtil_parser.add_argument("--type", type=str, choices=["stop", "pause"], default="pause", help="Action type: stop or pause")
    rununtil_parser.add_argument("--clear", action="store_true", help="Clear criteria and set default pause action")

    args = parser.parse_args()

    if args.command == "list":
        list_positions()
    elif args.command == "rununtil":
        run_until(args.position, args.runtime, args.pores, args.type, args.clear)


if __name__ == "__main__":
    main()
