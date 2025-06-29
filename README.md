## rf - A minimalist framework for reproducible computation

```
pip install git+https://github.com/apuapaquola/rf.git
```

## Preprint 

 http://biorxiv.org/content/early/2015/12/09/033654
 
## Overview

We propose a simple and intuitive way to organize computational analyses using a directory structure constructed according to 3 simple principles.

Consider the following directory structure:

    .
    └── nodeA
        ├── _c
        ├── _o
        ├── nodeB
        │   ├── _c
        │   └── _o
        └── nodeC
            ├── _c
            └── _o


In this tree, nodeA has two children: nodeB and nodeC.

We can think of these nodes as steps in a computational pipeline, in which nodeB and nodeC depend on the results of computation performed in nodeA.

This is principle 1: use of a directory structure to represent dependencies between analysis steps.

Each node has two special subdirectories: `_c` and `_o` with distinct purposes. We put documentation, code and other files that describe this analysis step in directory `_c`. For this reason, we call `_c` the "code" directory. Similarly, we use directory `_o` to store the results of computation of this analysis step. For this reason, we call `_o` the "output" directory.

This is principle 2: separation of user-generated data from program-generated data.

In the "code" directory we put a file named `run`. `run` is a script that is supposed to be run without arguments from the "code" directory. This script is responsible to call the necessary programs that will do the computation in the analysis step and generate the contents of `_o`.

This is principle 3: use of driver scripts. [doi: 10.1371/journal.pcbi.1000424]


These 3 principles are desirable to help keep analysis organized, reproducible and easier to understand.

A directory structure is a intuitive way to represent data dependencies. Let's say we are at some `_o` directory looking at output files, and we wonder how these files were generated. A pwd command will display the full path to that directory, which has a sequence of names of analysis steps involved in the generation of these files.

Separation of computer-generated data from human-generated data is also nice. It is a way to make sure that users don't edit output files. It is also useful to know which files are program-generated, so we know which files are OK to delete because they can be computed again.

Running driver scripts without arguments is a way to make sure computation doesn't depend on manually specified parameters, which are easy to forget.



## Version control

The separation of computer-generated data from human-generated data makes it easy to use version control systems for an analysis tree.

In the current implementation we use git for `_c` and git-annex for `_o`. For some operations that involve more than one call to git or git annex, we provide a wrapper command `rf`.

Using git, users can collaborate and share analyses trees in a similar they can do with code.


## Status

This framework is in early stage of development, and contributors are very welcome.


Current work includes, and some of these will be available soon:

* Apptainer and Docker support.
* More and better documentation.
* Concrete examples of analysis, mostly focusing on Bioinformatics.
* Use cases.
* Improvement of the manuscript.
* Support for git lfs.

## Contributing

Please do!

## License

GNU GPLv3
 