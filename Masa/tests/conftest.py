"""Define the necessary fixtures that will need to be used globally."""

from collections import namedtuple
from pathlib import Path
import uuid

from PySide2 import QtCore as qtc
import cv2
import numpy as np
import pytest

from .utils import DummyAnnotationsFactory, DummyBufferFactory, GUIFactory
from Masa.core.datahandler import TrackedObject, FrameData, DataHandler
from Masa.models import Buffer
# import cv2
import Masa.models.buffer


# Directories for Masa ########################################################
@pytest.fixture(name="dcpf", autouse=True, scope="session")
def data_center_path_file(tmp_path_factory) -> qtc.QSettings:
    """Initialized needed settings and directories for the Data Center.

    Create and return `QSettings` object with initialized values.
    """
    # TODO: Make this works on Windows too!!!
    masa_base = tmp_path_factory.mktemp("Masa")
    masa_dc = masa_base / "data_center"
    config = masa_base / ".config"

    settings = qtc.QSettings(str(config), qtc.QSettings.NativeFormat)
    settings.setValue("data_center", str(masa_dc))
    settings.sync()

    return settings


@pytest.fixture(scope="session")
def data_center_dir(dcpf):
    """Create and return the `data_center` directory."""
    dc = Path(dcpf.value("data_center", "", type=str))
    dc.mkdir()

    return dc


@pytest.fixture(scope="session")
def workspace_dir(data_center_dir):
    ws = data_center_dir / "test_workspace"
    ws.mkdir()

    return ws


@pytest.fixture(scope="function")
def empty_data_id_dir(workspace_dir):
    d_id = workspace_dir / str(uuid.uuid4())
    d_id.mkdir()

    return d_id


@pytest.fixture(scope="function")
def empty_data_dir(empty_data_id_dir):
    """Create and return the `data` dir."""
    data_dir = empty_data_id_dir / "data"
    data_dir.mkdir()

    return data_dir


@pytest.fixture(scope="function")
def empty_annotations_dir(empty_data_id_dir):
    """Create the annotations dir within the Data ID."""
    ann = empty_data_id_dir / "annotations"
    ann.mkdir()

    return ann

# Annotations related test data ################################################
# All of this uses data from `simple_anno`
simple_anno = DummyAnnotationsFactory.get_annotations("simple_anno")

@pytest.fixture(name="s_anno_rl", scope="session",
                params=simple_anno.data)
def simple_raw_annotations_loop(request):
    return simple_anno.head, request.param


@pytest.fixture(name="s_anno_rli", scope="session",
                params=simple_anno.data_per_instance)
def simple_raw_annotations_loop_per_instance(request):
    return simple_anno.head, request.param


AnnotationsSet = namedtuple("AnnotationsSet", "file head data")
@pytest.fixture(name="s_anno_rf",scope="function")
def simple_raw_annotations_file(empty_annotations_dir):
    return AnnotationsSet(simple_anno.create_file(empty_annotations_dir), simple_anno.head, simple_anno.data)


@pytest.fixture(scope="function")
def data_handler(s_anno_rf):
    dh = DataHandler(s_anno_rf.file)
    return dh

def tracked_objects_per_instance():
    head, data = simple_anno.head, simple_anno.data_per_instance
    tobjs = []
    for d in data:
        tobj = None
        _tobjs = []
        for instance in d:
            instance_dict = {}
            track_id = instance[head.index("track_id")]
            # print(instance)
            object_class = instance[head.index("object")]
            for h in head:
                if h not in ["track_id", "object"]:
                    instance_dict[h] = instance[head.index(h)]

            if tobj is None:
                tobj = TrackedObject(track_id, object_class, instance_dict)
            else:
                tobj.add_instance(instance_dict)

        tobjs.append(tobj)

    return tobjs


def tracked_objects():
    head, data = simple_anno.head, simple_anno.data
    tobjs = []
    for d in data:
        instance_dict = {}
        track_id = d[head.index("track_id")]
        object_class = d[head.index("object")]
        for h in head:
            if h not in ["track_id", "object"]:
                instance_dict[h] = d[head.index(h)]

        tobj = TrackedObject(track_id, object_class, instance_dict)

    tobjs.append(tobj)

    return tobjs


@pytest.fixture(name="s_tobj_l", scope="function",
                params=tracked_objects_per_instance())
def simple_tracked_object_loop(request):
    return request.param


# Video buffer related test data ##############################################
@pytest.fixture(name="ocv_video", scope="function")
def ocv_tagged_video(empty_data_dir):
    def vid(length=30, width=640, height=320):
        ocv_tagged_video = DummyBufferFactory.get_buffer("ocv_simple_tagged")
        ocv_tagged_video.length = length
        ocv_tagged_video.width = width
        ocv_tagged_video.height = height
        ocv_tagged_video.create_dummy_data(empty_data_dir)
        return ocv_tagged_video

    return vid

@pytest.fixture(name="m_buffer", scope="function")
def monkey_patched_buffer_class(monkeypatch):
    """Monkey patched `Masa.models.Buffer`.

    We want the `Buffer` to be able to receive our mocked video.
    """
    monkeypatch.setattr("Masa.models.buffer.cv2.VideoCapture", lambda x: x)
    return Buffer
    # print(getattr(Masa.models.buffer.cv2, "VideoCapture"))


# FrameData related test data #################################################


# GUI #########################################################################
@pytest.fixture(name="gui_imgb")
def gui_image_button(qtbot):
    image = np.zeros([240, 240, 3], np.uint8)
    imgb = GUIFactory.get_gui("image_button", image)
    imgb.show()
    qtbot.add_widget(imgb)
    return imgb
