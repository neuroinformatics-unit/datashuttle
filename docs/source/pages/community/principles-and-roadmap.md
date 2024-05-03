# Principles and Roadmap

In this document we lay out our vision for **datashuttle**, what
it aims to do and it's place in the data standardisation landscape.


## Principles of **datashuttle**

The three guiding principles in the development of **datashuttle** are:

1) It is not a rival or replacement for more developed specifications,
[BIDS](https://bids.neuroimaging.io/)
and
[NWB](https://www.nwb.org/).
It is instead a lightweight specification to get
started quickly with a standardised framework. BIDS / NWB are the gold
standard for standardised research outputs that should always be the final aim for a project.

2) It will require only the minimum amount of standardisation required
for specific goals.

3) It will be versioned and modular, meaning you can start with minimal
standardisation (and errort) and build up depending on your requirements.


### 1) Not a rival to existing standardisation / Always use existing standarards / align as closely as possible.

It is not a rival or replacement for more developed specifications,
[BIDS](https://bids.neuroimaging.io/)
and
[NWB](https://www.nwb.org/).

It is instead a lightweight specification to get
started quickly with a standardised framework. BIDS / NWB are the gold
standard for standardised research outputs that should always be the final aim for a project.

The guiding rule is that some standardisation is better than no standardisation.
If you are busy, you can use NeuroBlueprint and datashuttle to maintain
standardisation in your project folder, and consider extension to full
standardisation later. If you are already acquiring data in a fully standardised
format, even if it is not NWB or BIDS, then NeuroBlueprint / **datashuttle**
is not for you.


### 2) It will be as minimalistic as possible sufficient for automated preprocessing and analysis

[NeuroBlueprint]() aims to be a lightweight specification. As times goes on,
we will be careful to maintain few restrictions as possible to keep it's purpose
clear and avoid simple duplication of existing, more detailed standards.

Developed by the Neuroinformatics unit, our primary objective in standardisation
is to faciliatte automated preprocessing and analysis pipelines. NeuroBlueprint
and DataShuttle will be structured in a way that new restrictions will
be added only if they are required for the automation of preprocessing and
analysis pathways. Further, they will be optional based on the kind of analysis you will run.

In version 1XX, the initial goal was simple: 'have project folders standardised
sufficiently that it is clear where all collected data is and stored predictably
across projects'. This alone opens many doors for automated preprocessing
of data.

Later, we will want to support additional analysis that will require additional
standardisation. For example, you may be running an experiment
in which you need to align timestamps across behavioural and electrophysiological data.
For automated analysis, metadata standards for syncrnousatio pulses will be required.
We will add only the requirements required for this goal and document them in
a clear way that only IF you want to do such automated analysis THEN
you should use this rule.

We hope by an objective-based approach projects will incrementally move
towards full BIDS and NWB standardisation across their projects.

### It will be versioned and modular

Linked strongly to point 3) we will ensure that datashuttle and
NeuroBlueprint are designed in a modular way.


## Roadmap for the future

- metadata
- working with BIDS / NWB to align as closely as possible
-  support different experiment types
- maintain and add quality of life features as requested.
- add docstring versioning to datashuttle and NeuroBlueprint docs prior to new version release.
