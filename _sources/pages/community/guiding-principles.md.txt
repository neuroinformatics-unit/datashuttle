# Guiding Principles

In this document we lay out our vision for
[**NeuroBlueprint**](https://neuroblueprint.neuroinformatics.dev/)
and **datashuttle** through three guiding principles.

For additional detail, please refer to our blog posts motivating
[**NeuroBlueprint**](https://neuroinformatics.dev/blog/neuroblueprint.html)
and
[**datashuttle**](https://neuroinformatics.dev/blog/datashuttle.html).

The three guiding principles driving the development of
**NeuroBlueprint**
and **datashuttle** are:

## Align with existing community initiatives

[BIDS](https://bids.neuroimaging.io/)
and
[NWB](https://www.nwb.org/)
are the most comprehensive community standards for systems neuroscience projects.
Adhering to these specifications ensures complete standardisation e.g. in metadata
and file formats. Though extremely valuable, full compliance with these standards
can be time-consuming and technically difficult.

**NeuroBlueprint**'s role is to provide a lightweight standard that can be used to get
started, especially during the early phase of a project when things may be very busy.
The guiding principle is that some standardisation is better than no standardisation.

**NeuroBlueprint** is not intended as a rival or replacement for more established
specifications, but rather as a stepping stone towards full standardisation.
We aim to align as closely as possible to the BIDS specification and in future
to provide conversion to NWB through **datashuttle**.

## Strive to be lightweight

**NeuroBlueprint** aims to keep the specification as lightweight
as possible. There is no benefit in the specification proliferating
as it develops such that it ends up duplicating BIDS in scope.

In the initial versions (**datashuttle** v0.4, **NeuroBlueprint** v0.2),
the goal is to have a simple organisational
system in which the raw data for different datatypes (e.g. ephys, behaviour)
can be automatically discovered in any given project.

In future versions it will be necessary to standardise additional features
(e.g. sync pulse metadata) to allow automation of more sophisticated analyses.
New standards will always be goal-orientated and customisable, only required
to achieve a particular research goal. It is anticipated that as these 'rules'
are adopted, projects will become progressively easier to convert to BIDS or NWB.

The role of **datashuttle** will be to enforce these rules in a flexible manner.

## Keep releases versioned and modular

**NeuroBlueprint** and **datashuttle** will be
properly versioned and modular, enabling smooth development over time.
New versions will prioritize backward compatibility, with changes that break
compatibility occurring infrequently and only aimed at enhancing alignment with existing standards.

Typically, new versions will include new
sets of standardisation rules,
which users may choose to adopt or not. **datashuttle** will
enforce these in a flexible way, with efforts being
made to minimise changes to its API as much as possible.
