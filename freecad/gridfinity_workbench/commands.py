"""Gridfinity workbench commands module.

Contains command objects representing what should happen on a button press.
"""

# ruff: noqa: D101, D102, D107, N802

import re
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import FreeCAD as fc  # noqa: N813
import FreeCADGui as fcg  # noqa: N813

from . import custom_shape, features, utils

if TYPE_CHECKING:
    import Part

ICONDIR = Path(__file__).parent / "icons"

PASCAL_CASE_REGEX = re.compile(r"(?<!^)(?=[A-Z])")


class ViewProviderGridfinity:
    """Gridfinity workbench viewprovider."""

    def __init__(self, obj: fcg.ViewProviderDocumentObject, icon_path: str) -> None:
        # Set this object to the proxy object of the actual view provider
        obj.Proxy = self
        self._check_attr()
        self.icon_path = icon_path or str(ICONDIR / "gridfinity_workbench_icon.svg")

    def _check_attr(self) -> None:
        """Check for missing attributes.

        Required to set icon_path when reopening after saving.
        """
        if not hasattr(self, "icon_path") or not Path(self.icon_path).exists():
            self.icon_path = str(ICONDIR / "gridfinity_workbench_icon.svg")

    def attach(self, vobj: fcg.ViewProviderDocumentObject) -> None:
        """Attach viewproviderdocument object to self."""
        self.vobj = vobj

    def getIcon(self) -> str:
        """Get icons path."""
        self._check_attr()
        return self.icon_path

    def dumps(self) -> dict:
        """Needed for JSON Serialization when saving a file containing gridfinity object."""
        self._check_attr()
        return {"icon_path": self.icon_path}

    def loads(self, state: dict) -> None:
        """Needed for JSON Serialization when saving a file containing gridfinity object."""
        if state and "icon_path" in state:
            self.icon_path = state["icon_path"]


class BaseCommand:
    """Base for gridfinity workbench command.

    A command should derive from this BaseCommand class.

    """

    def __init__(
        self,
        *,
        name: str,
        pixmap: Path,
        menu_text: str,
        tooltip: str,
    ) -> None:
        self.name = name
        self.pixmap = pixmap
        self.menu_text = menu_text
        self.tooltip = tooltip

    def IsActive(self) -> bool:
        """Check if command should be active."""
        return fc.ActiveDocument is not None

    def Activated(self) -> None:
        """Execute when command is activated."""
        raise NotImplementedError

    def GetResources(self) -> dict[str, str]:
        """Get command resources."""
        return {
            "Pixmap": str(self.pixmap),
            "MenuText": self.menu_text,
            "ToolTip": self.tooltip,
        }


class CreateCommand(BaseCommand):
    """Base for gridfinity workbench command.

    Used for commands that always create an object.

    """

    def __init__(
        self,
        *,
        name: str,
        gridfinity_function: type[features.FoundationGridfinity],
        pixmap: Path,
    ) -> None:
        super().__init__(
            name=name,
            pixmap=pixmap,
            menu_text=f"Gridfinity {PASCAL_CASE_REGEX.sub(' ', name)}",
            tooltip=f"Create a Gridfinty {PASCAL_CASE_REGEX.sub(' ', name)}.",
        )
        self.gridfinity_function = gridfinity_function

    def Activated(self) -> None:
        """Execute when command is activated."""
        obj = utils.new_object(self.name)
        if fc.GuiUp:
            view_object: fcg.ViewProviderDocumentObject = obj.ViewObject
            ViewProviderGridfinity(view_object, str(self.pixmap))

        self.gridfinity_function(obj)

        fc.ActiveDocument.recompute()
        fcg.SendMsgToActiveView("ViewFit")


class CreateBinBlank(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="BinBlank",
            gridfinity_function=features.BinBlank,
            pixmap=ICONDIR / "BinBlank.svg",
        )


class CreateBinBase(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="BinBase",
            gridfinity_function=features.BinBase,
            pixmap=ICONDIR / "BinBase.svg",
        )


class CreateSimpleStorageBin(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="SimpleStorageBin",
            gridfinity_function=features.SimpleStorageBin,
            pixmap=ICONDIR / "SimpleStorageBin.svg",
        )


class CreateEcoBin(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="EcoBin",
            gridfinity_function=features.EcoBin,
            pixmap=ICONDIR / "eco_bin.svg",
        )


class CreatePartsBin(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="PartsBin",
            gridfinity_function=features.PartsBin,
            pixmap=ICONDIR / "parts_bin.svg",
        )


class CreateBaseplate(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="Baseplate",
            gridfinity_function=features.Baseplate,
            pixmap=ICONDIR / "Baseplate.svg",
        )


class CreateMagnetBaseplate(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="MagnetBaseplate",
            gridfinity_function=features.MagnetBaseplate,
            pixmap=ICONDIR / "magnet_baseplate.svg",
        )


class CreateScrewTogetherBaseplate(CreateCommand):
    def __init__(self) -> None:
        super().__init__(
            name="ScrewTogetherBaseplate",
            gridfinity_function=features.ScrewTogetherBaseplate,
            pixmap=ICONDIR / "screw_together_baseplate.svg",
        )


class DrawCommand(BaseCommand):
    """Base for gridfinity workbench command.

    Used for commands where an object is drawn.

    """

    def __init__(
        self,
        *,
        name: str,
        pixmap: Path,
        menu_text: str,
        tooltip: str,
        gridfinity_functions: OrderedDict[str, Any],
    ) -> None:
        super().__init__(
            name=name,
            pixmap=pixmap,
            menu_text=menu_text,
            tooltip=tooltip,
        )
        self.gridfinity_functions = gridfinity_functions

    def Activated(self) -> None:
        dialog_data = custom_shape.custom_bin_dialog(list(self.gridfinity_functions.keys()), None)
        if dialog_data is None:
            return
        assert dialog_data.bin_type is not None
        assert dialog_data.bin_type in self.gridfinity_functions

        obj = utils.new_object(self.name)
        if fc.GuiUp:
            view_object: fcg.ViewProviderDocumentObject = obj.ViewObject
            ViewProviderGridfinity(view_object, str(self.pixmap))

        self.gridfinity_functions[dialog_data.bin_type](obj, dialog_data.layout)

        fc.ActiveDocument.recompute()
        fcg.SendMsgToActiveView("ViewFit")


class DrawBin(DrawCommand):
    def __init__(self) -> None:
        super().__init__(
            name="CustomBin",
            pixmap=ICONDIR / "CustomBin.svg",
            menu_text="Gridfinity Custom Bin",
            tooltip="Draw a custom gridfinity bin of any type.",
            gridfinity_functions=OrderedDict(
                [
                    ("Blank Bin", features.CustomBlankBin),
                    ("Bin Base", features.CustomBinBase),
                    ("Storage Bin", features.CustomStorageBin),
                    ("Eco Bin", features.CustomEcoBin),
                ],
            ),
        )


class DrawBaseplate(DrawCommand):
    def __init__(self) -> None:
        super().__init__(
            name="CustomBaseplate",
            pixmap=ICONDIR / "CustomBaseplate.svg",
            menu_text="Gridfinity Custom Baseplate",
            tooltip="Draw a custom gridfinity baseplate of any type.",
            gridfinity_functions=OrderedDict(
                [
                    ("Simple Baseplate", features.CustomBaseplate),
                    ("Magnet Baseplate", features.CustomMagnetBaseplate),
                    ("Screw Together Baseplate", features.CustomScrewTogetherBaseplate),
                ],
            ),
        )


class ChangeLayout(BaseCommand):
    def __init__(self) -> None:
        super().__init__(
            name="ChangeLayout",
            pixmap=ICONDIR / "ChangeLayout.svg",
            menu_text="Change layout",
            tooltip=("Change the layout of an existing custom shape."),
        )

    def IsActive(self) -> bool:
        selection = fcg.Selection.getSelection()
        return len(selection) == 1 and hasattr(selection[0].Proxy, "layout")

    def Activated(self) -> None:
        obj = fcg.Selection.getSelection()[0]

        dialog_data = custom_shape.custom_bin_dialog([], obj.Proxy.layout)
        if dialog_data is None:
            return
        assert dialog_data.bin_type is None

        obj.Proxy.layout = dialog_data.layout
        obj.recompute()


class StandaloneLabelShelf(BaseCommand):
    def __init__(self) -> None:
        super().__init__(
            name="StandaloneLabelShelf",
            pixmap=ICONDIR / "PlaceLabelShelf.svg",
            menu_text="Standalone label shelf",
            tooltip=(
                "Create a standalone label shelf.<br><br>"
                "Select any Gridfinity Bin face and run this command to create a label shelf"
                "attached to selected face."
            ),
        )

    def IsActive(self) -> bool:
        selection = fcg.Selection.getSelectionEx()
        if len(selection) != 1 or len(selection[0].SubObjects) != 1:
            return False
        obj = selection[0].Object
        if not hasattr(obj, "Baseplate") or obj.Baseplate:
            return False
        face = selection[0].SubObjects[0]
        if not hasattr(face, "ShapeType") or face.ShapeType != "Face":
            return False
        if face.findPlane() is None:
            return False
        points = [v.Point for v in face.Vertexes]
        height = max([p.z for p in points])
        max_points = [p for p in points if p.z > height - 1e-4]
        return len(max_points) == 2  # noqa: PLR2004

    def Activated(self) -> None:
        obj = utils.new_object("LabelShelf")
        if fc.GuiUp:
            view_object: fcg.ViewProviderDocumentObject = obj.ViewObject
            ViewProviderGridfinity(view_object, str(ICONDIR / "BinBlank.svg"))

        selection = fcg.Selection.getSelectionEx()
        target_obj: fc.DocumentObject = selection[0].Object
        face: Part.Face = selection[0].SubObjects[0]

        features.StandaloneLabelShelf(obj, target_obj, face)

        fc.ActiveDocument.recompute()
