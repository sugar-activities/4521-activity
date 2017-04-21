import gtk


# Class for a colored VBox
class VBoxColor(gtk.VBox):
	
	def __init__(self, color, homogeneous=False, spacing=0):
		"Set up the vbox"
		super(VBoxColor, self).__init__(homogeneous, spacing)
		self.connect("expose-event", self.expose)
		self.color = color
		

	def expose(self, widget, event):
		"Draw the background"
		gc = widget.window.cairo_create()      
		gc.set_source_rgb(*self.color)
		gc.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
		gc.fill()