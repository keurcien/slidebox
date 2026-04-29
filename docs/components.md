# Components

Every component is a Pydantic model. Every container is a context manager.
Nesting inside a `with` block auto-wires parent/child relationships.

## Containers

| Component    | Description                                  |
| ------------ | -------------------------------------------- |
| `Presentation` | The deck itself. Root context manager.    |
| `Slide`      | One page. Child of Presentation.             |
| `Row`        | Horizontal flex container.                   |
| `Col`        | Vertical flex container.                     |
| `Grid`       | Fixed-column grid.                           |
| `Shape`      | Filled/bordered rectangle, ellipse, etc.     |

## Leaves

| Component | Description                    |
| --------- | ------------------------------ |
| `Text`    | A block of text.               |
| `Title`   | `Text(style='h1')` shortcut.   |
| `Subtitle`| `Text(style='subtitle')`.      |
| `Heading` | `Text(style='h2')` shortcut.   |
| `Image`   | Picture from a URL.            |
| `Spacer`  | Consumes flex space.           |

## Composites

| Component | Description                                      |
| --------- | ------------------------------------------------ |
| `Kpi`     | Label + big value + optional trend indicator.    |

Custom composites: subclass `ContainerComponent`, implement `build()` to
populate children declaratively.

```python
from slidebox.components.base import ContainerComponent
from slidebox import Shape, ShapeType, Text, Col

class BrandCard(ContainerComponent):
    message: str = ""
    accent: str = "#ff5a5f"

    def build(self) -> None:
        with Shape(shape_type=ShapeType.ROUND_RECTANGLE, fill=self.accent):
            with Col(gap=12, padding=20):
                Text(self.message, color="#ffffff")
```

## Universal fields

Every component accepts:

- `id="..."`  — deterministic object id. Use to target the element with `Updater`.
- `metadata={...}` — round-tripped in Google's alt-text so downstream tools can identify the element's origin.
- `raw={...}` — shallow-merged into the generated API request. Use only for properties slidebox hasn't yet wrapped.
