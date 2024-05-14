# Guiding Principles

In this document we lay out our vision for
[**NeuroBlueprint**](https://neuroblueprint.neuroinformatics.dev/)
and **datashuttle** in three guiding principles.

For more detail, please see our blog posts motivating
[NeuroBlueprint](https://neuroinformatics.dev/blog/neuroblueprint.html)
and
[**datashuttle**](https://neuroinformatics.dev/blog/datashuttle.html).

The three guiding principles in the development of
**NeuroBlueprint**
and **datashuttle** are:

## 1) Align as best possible with existing community initiatives (BIDS and NWB)

[BIDS](https://bids.neuroimaging.io/)
and
[NWB](https://www.nwb.org/)
are the gold-standard for standardising systems neuroscience projects.
Alignment with these specifications should always be the final aim for a project.

The role of **NeuroBlueprint** is a lightweight standard that can be used to get
started, especially during the early phase of a project when you may be very busy.
The guiding rule is that some standardisation is better than no standardisation.

It is not a rival or replacement for more developed specifications,
but a stepping stone towards full standardisation.
We aim to align with BIDS specification and in future to provide
conversion to NWB through **datashuttle** wherever possible.

## 2) Strive to be as lightweight as possible

In keeping with **(1)**, **NeuroBlueprint** aims to keep the specification as lightweight
as possible. There is no point in the standard proliferating in scope such that it becomes
a duplicate of BIDS and NWB.

In the first version (**datashuttle 0.4, **NeuroBlueprint 0.2),
the goal is to have a simple organisational
system in which different datatypes (ephys, behaviour) can be
automatically found in any project.

In future versions as we extend the sophisiatication of automated analysis it will
be necessary to standardise additional features (e.g. sync pulse metadata).
These restrictions will always be goal-orientated and cumstomisable
to achieve your research goal. It is hoped as these 'rules' are
accumulated projects become closer and closer to full BIDS standardisation.

The role of **datashuttle** will be to enforce these rules in a flexible way.

## 3) Be versioned and modular

Linked to **(2)**,  **NeuroBlueprint** and **datashuttle** will be
properly versioned and modular, allowing them to develop smoothly over time.
The release of a new versions will strive hard to be backwards compatible,
only breaking backwards compatibility infrequently to improve alignment
with existing standards.

Typically, new versions will only include new
sets of standardisation rules that
you may or may not choose to follow. **datashuttle** will
enforce these in a flexible way and care will be taken to ensure its API
changes as little as possible.
