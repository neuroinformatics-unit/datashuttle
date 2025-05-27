:html_theme.sidebar_secondary.remove:

<!-- We want to have a centered title, which is difficult in sphinx without centering
the entire page. We need the title here otherwise the tab title defaults to <no-title>.
Therefore, add the title and hide it, then add a custom centered title.
-->

```{raw} html
<div style="height: 0; visibility: hidden;">
```
# datashuttle
```{raw} html
</div>
```

<p style="text-align: center; font-size: 48px;"><b>datashuttle</b></p>
<p style="text-align: center; font-size: 22px;">Automate the creation, validation and transfer of neuroscience project folders.</p>

```{image} _static/datashuttle-overview-light.png
:alt: My Logo
:class: logo, mainlogo, only-light
:align: center
:width: 600px
```
```{image} _static/datashuttle-overview-dark.png
:alt: My Logo
:class: logo, mainlogo, only-dark
:align: center
:width: 600px
```
<br>


::::{grid} 1 2 2 4
:gutter: 4


:::{grid-item-card} Get started
:link: pages/get_started/index
:link-type: doc

Get started with ``datashuttle``
:::


:::{grid-item-card} User guides
:link: pages/user_guides/index
:link-type: doc

Explore ``datashuttle``'s features
:::

:::{grid-item-card} Examples
:link: pages/examples/index
:link-type: doc

``datashuttle`` in the real world
:::

:::{grid-item-card} Python API
:link: pages/api_index
:link-type: doc

Full Python reference
:::

::::

A lack of project standardization in systems neuroscience
[hinders data sharing and collaboration](https://neuroinformatics.dev/blog/neuroblueprint.html),
creating barriers to reproducibility and scientific progress.

``datashuttle`` helps standardise experimental
projects by automating folder creation and transfer
during acquisition and analysis. Its graphical interface or Python API builds
folder trees according to the [NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev)
specification. Automation and validation ensures that no errors, such as duplicate session
names or incorrect dates, slip into the project.

Data can be transferred between acquisition, storage and analysis
machines with a single function call or button click. Standardisation makes
folder names predictable, meaning it is easy to transfer specific combinations
of subjects, sessions or data-types with ``datashuttle``.

Folders are standardised to the
[NeuroBlueprint](https://neuroblueprint.neuroinformatics.dev) specification:

```{image} /_static/NeuroBlueprint_project_tree_dark.png
   :align: center
   :class: only-dark
   :width: 550px
```
```{image} /_static/NeuroBlueprint_project_tree_light.png
   :align: center
   :class: only-light
   :width: 550px
```

Dive in with our [Getting Started page](pages/get_started/index)
or targeted [User Guides](pages/user_guides/index).

Have questions, issues or feedback? Get in contact through
[GitHub issues](https://github.com/neuroinformatics-unit/datashuttle/issues)
or our
[Zulip chat.](https://neuroinformatics.zulipchat.com/#narrow/stream/405999-DataShuttle)

```{toctree}
:maxdepth: 2
:caption: index
:hidden:

pages/get_started/index
pages/user_guides/index
pages/examples/index
pages/community/index
pages/api_index
```
