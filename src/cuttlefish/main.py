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

def run_until(position_index, runtime, pores):
    manager = Manager()
    positions = list(manager.flow_cell_positions())
    
    try:
        selected_position = positions[position_index]
    except IndexError:
        print("Invalid position index. Use 'cuttlefish list' to see available positions.")
        return

    connection = selected_position.connect()
    protocols = connection.protocol.list_protocol_runs()
    protocol_id = protocols.run_ids[-1]
    run_info = connection.protocol.get_run_info(run_id=protocol_id)
    acquisition_run_id = run_info.acquisition_run_ids[-1]

    criteria = CriteriaValues(
        runtime=runtime,
        available_pores=pores
    )

    pause_criteria_protobuf = criteria.as_protobuf()
    connection.run_until.write_target_criteria(
        acquisition_run_id=acquisition_run_id, 
        pause_criteria=pause_criteria_protobuf
    )
    print("RunUntil criteria set successfully.")

def main():
    parser = argparse.ArgumentParser(prog="cuttlefish", description="Control nanopore devices with MinKNOW API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List available flow cell positions")

    # RunUntil command
    rununtil_parser = subparsers.add_parser("rununtil", help="Set RunUntil criteria")
    rununtil_parser.add_argument("--position", type=int, required=True, help="Index of the flow cell position")
    rununtil_parser.add_argument("--runtime", type=int, required=True, help="Runtime in seconds")
    rununtil_parser.add_argument("--pores", type=float, required=True, help="Available pores threshold (percentage)")

    args = parser.parse_args()

    if args.command == "list":
        list_positions()
    elif args.command == "rununtil":
        run_until(args.position, args.runtime, args.pores)

if __name__ == "__main__":
    main()
