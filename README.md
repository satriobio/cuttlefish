# Cuttlefish

Change Nanopore run protocol on the fly (or swim)

![alt text](cuttlefish.gif)

## Quick start

List device index

```
cuttlefish list
```

Rununtil

```
cuttlefish rununtil --position 0 --type pause --pores 2000 --runtime 3600
```

This will pause sequencing when pore number reach 2000 pores or runtime reach 3600 seconds.


Clear rununtil

```
cuttlefish rununtil --position 0 --clear
```

This will clear rununtil settings and resume sequencing (if paused).

## Installation

```
git clone https://github.com/satriobio/cuttlefish.git
cd cuttlefish
conda env create -f env.yml
```

## To Do

- [ ] Add more functionalites from MinKNOW api
- [ ] Rework gui

## License

GNU General Public License v3.0