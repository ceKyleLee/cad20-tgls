# GPU Accelerated Logic Re-simulation
This is the 3rd place solution to the [ICCAD 2020 CAD contest problem C](http://iccad-contest.org/2020/), which performs timing-aware gate-level logic simulation on GPU, imporves the efficiency comparing to the the past implemetation on large designs. 

This task is seperated into two parts: (1) Graph Preprocessing and (2) GPU Simulation. First (1) generates a intermediate file by input the gate level netlist design with corresponding timing info and behavior library, then (2) can perform simulation base on the previous file and another input testbench contains waveforms of the primary and pseudo-primary inputs of the design. The output is a SAIF file which contains the time nets were of value 0, 1, x, or z for nets in the design for the duration of the specified timestamps.

## 1. How to Build
Download the source code. For example,
```bash
$ git clone https://github.com/ceKyleLee/cad20-tgls.git
```
### 1.1 Dependencies
- GCC (version >= 7.5.0)
- CUDA (version >= 11.0)
- Python (version >= 3.6)
- GNU Make (version >= 4.1)
- Pyinstaller (version >= 3.6) (Optional, for preprocessor building)
### 1.2 Build Preprocessor 
Preprocessor is based on *Python*, to build a binary executable file, please following the instructions below:
```bash
$ cd cad20-tgls/Preprocess
$ bash build.sh
```
For more building details please refers to [`Preprocess/build.sh`](build.sh).

### 1.3 Build Simulator
```bash
$ cd cad20-tgls/Simulation
$ make
```
For more detail please refer to [`Simulation/makefile`](Simulation\makefile).

## 2. How to Run
**step 1**: Graph Preprocessing
Preprocessor requires three input:
- **netlist.gv**: A gate level netlist description of the design.
- **netlist.sdf**: Describes the delays of each gate in the design.
- **std_cells.vlib**: A standard cell library, which describes the behavior of each standard cell gate in the
design.
- **intermediate**: Name of the output intermediate file.

To perform graph preprocessing, please run:
```bash
$ cd cad20-tgls
$ ./Preprocess/GraphPreprocessor <netlist.gv> <netlist.sdf> <std_cells.vlib> [intermediate]
```
*Please be aware, this step may takes about 1 hour.(more then 2 hours for larger design.)
For toy test, please run:
```bash
$ cd cad20-tgls
$ ./Preprocess/GraphPreprocessor Simulation/toy/NV_NVDLA_partition_o_GEN.gv Simulation/toy/NV_NVDLA_partition_o_GEN.sdf Simulation/toy/GENERIC_STD_CELL.vlib Simulation/toy/intermediate.file
```
**step 2**: GPU simulator
Simulator requires five inputs:
- **intermediate**: Intermediate file generated in the previous step.
- **input.vcd**: Contains waveforms of the primary and pseudo-primary inputs of the design.
- **dumpon_time**, **dumpoff_time**: The specified timestamps(ps) for the duration of dumped saif file.
- **result.saif**: Name of the output file.

To perform graph preprocessing, please run:
```bash
$ cd cad20-tgls
$ ./Simulation/bin/GPUsimulator <intermediate> <input.vcd> <dumpon_time> <dumpoff_time> [result.saif]
```

For toy test, please run:
```bash
$ cd cad20-tgls
$ ./Simulation/bin/GPUsimulator Simulation/toy/intermediate.file Simulation/toy/NV_NVDLA_partition_o_dc_24x33x55_5x5x55x25_int8_input.vcd 0 2972036001 Simulation/toy/result.saif
```

***Note**: Following the contest instruction 
1. SDF file should only include the ABSOLUTE and IOPATH keywords for consideration.
2. VCD file were reformatted for the consistency sake. (Please refer to [QA38](http://iccad-contest.org/2020/Problem_C/Problem%20C_QA_0928.pdf))
For more information, please refer to [Problem Introduction documentation](http://iccad-contest.org/2020/Problem_C/ICCAD2020_ContestProblemSpecification_ProblemC_08102020.pdf) of the contest.

## 3. Modules
**Preprocess**:
- `SDF`: parser for delay timing file(.sdf)
- `VLIB`: parser for standard cell library file(.vlib)
- `NETLIST`: parser for netlist, which integrate data from parser in `SDF` and `VLIB` to form the whole netilst and generate intermediate file
- `util`: some utility code

**Simulation**:
- `src`: C++ source code
    - `gate`: database for gates in designs, which stores timing and behaviour information of the cell
    - `parser`: parse the intermediate file and waveforms from testbench file(.vcd), and generate output file(.saif)
    - `sim`: perform simulation on gpu
    - `wave`: database for waveforms in testbench and simulation result
    - `util`: some utility code
- `toys`: toy test cases, the smallest testbench `NV_NVDLA_partition_o_dc_24x33x55_5x5x55x25_int8` provided by contest.

## 4. Results
Experiments are performed on Amazon EC2 G4 instances, powered by 2nd Generation Intel Xeon Scalable (Cascade Lake) CPU (2.5GHz/16 cores), NVIDIA T4 GPUs(16 GB memory) and 64 GB memory. Consistent with the contest, 16 threads are used. 
These testbenches can be downloaded from [problem description page of ICCAD'20 contest](http://iccad-contest.org/2020/problems.html)

design                                            | Elapsed Time (s) | Speedup times |
:------------------------------------------------:|-----------------:|--------------:|
`ExampleRocketSystem_DefaultConfig_rando`         | 17.2             | 5.67          |
`ExampleRocketSystem_TinyConfig_median`           | 15.2             | 3.68          |
`ExampleRocketSystem_TinyConfig_rando`            | 15               | 4.4           |
`NV_NVDLA_partition_c_dc_24x33x55_5x5x55x25_int8` | 10.4             | 1.95          |
`NV_NVDLA_partition_m_dc_24x33x55_5x5x55x25_int8` | 14.1             | 8.03          |
`NV_NVDLA_partition_m_rando`                      | 59.8             | 14.07         |
`NV_NVDLA_partition_o_dc_24x33x55_5x5x55x25_int8` | 7.7              | 1.04          |

***Elapsed time** only consider the run time of *GPUsimulator*.



