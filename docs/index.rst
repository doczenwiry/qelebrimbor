========
Overview
========

------------
Installation
------------

The tool can be installed by cloning the repository to a suitable location.

.. code-block:: bash

    git clone https://github.com/doczenwiry/qelebrimbor
    cd qelebrimbor

``qelebrimbor`` currently operates on a limited dataset of random ZX-graphs made of CNOT gates using PyZX.
In order to generate the dataset after cloning, you can issue the following command:

.. code-block:: bash

    uv run benchmarking/generate-dataset-rings-small.py

This will populate the directory benchmarking/datasets/small/identity with all the input ZX-graphs.

At this stage, it is possible to benchmark the prototype against the entire dataset.

.. code-block:: bash

    uv run benchmarking/benchmark-dataset-rings-small.py

The benchmark will invoke the main tool, ``qb``, on each ZX-graph from the dataset and print a summary of the outcome of the construction.

Alternatively, the prototype can be executed on a single ZX-graph from the dataset for more detailed information and visualize the constructed blockgraph

.. code-block:: bash

    uv run qb.py -v benchmarking/benchmark/datasets/small/identity/random-cnots-q4-d8-s2712719750.pyzx.json

--------
Pipeline
--------

The tool ``qb`` works by going through five stages;

1. Preliminary analysis
2. Preprocessing stage
3. Inflation stage
4. Reporting stage
5. Equivalence validation stage

Preliminary analysis
====================

Preprocessing stage
===================

Inflation stage
===============

Reporting stage
===============

Equivalence validation stage
============================