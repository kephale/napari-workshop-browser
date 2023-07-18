import numpy as np

from napari_workshop_browser import WorkshopWidget


# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams
def test_workshop_widget(make_napari_viewer, capsys):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100)))

    # create our widget, passing in the viewer
    my_widget = WorkshopWidget(viewer)

    viewer.window.add_dock_widget(my_widget)

    # We only test whether we can instantiate the widget and add to window
    assert my_widget is not None
