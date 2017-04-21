#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Base import
import gtk
import pango
import logging
from gettext import gettext as _
from urlparse import urlparse

# Local import
from src.person import Person
from src.union import Union
from src.tree import Tree
from src.tree import empty_tree, sample_family1, sample_family2
from vboxcolor import VBoxColor
import src.const as const


# Sugar import
try:
	from sugar.activity import activity
	from sugar.graphics.toolbutton import ToolButton
	from sugar.presence import presenceservice
	from gtk import Toolbar
	const.inSugar = True
except ImportError:
	from sugardummy import *
	const.inSugar = False


# Init position
const.tree_initx = (875 - const._person_width) / 2
const.tree_inity = (780 - const._person_height) / 2
const.bg_color = (0.7, 0.7, 0.7)

		
# Init log	
_logger = logging.getLogger('roots-activity')
_logger.setLevel(logging.DEBUG)
_consolehandler = logging.StreamHandler()
_consolehandler.setLevel(logging.DEBUG)
_consolehandler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
_logger.addHandler(_consolehandler)


# Init presence
presenceService = presenceservice.get_instance()
buddyName = presenceService.get_owner().props.nick


# Activity class
class RootsActivity(activity.Activity):

	def __init__(self, handle):
		"Set up the activity."
		
		# Sugar init
		activity.Activity.__init__(self, handle)
		
		# Create toolbox
		toolbox = activity.ActivityToolbox(self)
		toolbarview = Toolbar()
		tool = ToolButton('zoom-out')
		tool.set_tooltip(_('Zoom out'))
		tool.set_accelerator(_('<ctrl>minus'))
		tool.connect('clicked', self.zoom_out)
		toolbarview.insert(tool, -1)
		tool = ToolButton('zoom-in')
		tool.set_tooltip(_('Zoom in'))
		tool.set_accelerator(_('<ctrl>equal'))
		tool.connect('clicked', self.zoom_in)
		toolbarview.insert(tool, -1)
		toolbox.add_toolbar(_('View'), toolbarview)
		toolbarsample = Toolbar()
		tool = ToolButton('emptytree')
		tool.set_tooltip(_('Empty tree'))
		tool.connect('clicked', self.emptytree)
		toolbarsample.insert(tool, -1)
		tool = ToolButton('sample1')
		tool.set_tooltip(_('Test'))
		tool.connect('clicked', self.sample1)
		toolbarsample.insert(tool, -1)
		tool = ToolButton('sample2')
		tool.set_tooltip(_('Napoléon'))
		tool.connect('clicked', self.sample2)
		toolbarsample.insert(tool, -1)
		toolbox.add_toolbar(_('Samples'), toolbarsample)
		self.set_toolbox(toolbox)
		toolbox.show()

		# Create drawing area
		self.zoomlevel = 0
		self.area = gtk.DrawingArea()
		self.area.set_size_request(875, 780)
		self.area.set_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.BUTTON_RELEASE_MASK|gtk.gdk.BUTTON_MOTION_MASK|gtk.gdk.POINTER_MOTION_MASK)
		self.area.connect("expose_event", self.area_expose_cb)
		self.area.connect("button_press_event", self.press_button)
		self.area.connect("button_release_event", self.release_button)
		self.area.connect("motion_notify_event", self.mouse_move)
		self.moving = False
				
		# Create detail view
		self.fixed = VBoxColor(const.bg_color)
		self.fixed.set_size_request(325, 780)
		self.imagezone = gtk.DrawingArea()
		self.imagezone.set_size_request(325, 240)
		self.imagezone.set_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.BUTTON_RELEASE_MASK)
		self.imagezone.connect("expose_event", self.image_expose)
		self.imagezone.connect("button_press_event", self.image_release_button)
		self.image_paste = gtk.gdk.pixbuf_new_from_file("images/edit-paste.svg")
		self.image_hand1 = gtk.gdk.pixbuf_new_from_file("images/hand1.png")
		self.fixed.pack_start(self.imagezone, False, False, 0)
		self.detail_name = gtk.Entry()
		self.detail_name.connect("changed", self.detail_changed)
		self.fixed.pack_start(self.detail_name, False, False, 0)		
		radiocontainer = gtk.HBox()
		self.detail_chkmale = gtk.RadioButton(None, _("Male"))
		self.detail_chkmale.connect("toggled", self.sexradio_checked, 'M')
		radiocontainer.pack_start(self.detail_chkmale, True, True, 0)
		self.detail_chkfemale = gtk.RadioButton(self.detail_chkmale, _("Female"))
		self.detail_chkfemale.connect("toggled", self.sexradio_checked, 'F')		
		radiocontainer.pack_start(self.detail_chkfemale, True, True, 0)
		self.fixed.pack_start(radiocontainer, False, False, 0)
		scrolled = gtk.ScrolledWindow()
		scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scrolled.set_border_width(2)
		self.detail_description = gtk.TextView()
		self.detail_description.set_wrap_mode(gtk.WRAP_WORD)
		self.detail_description.set_size_request(200, 100)
		self.detail_description.set_cursor_visible(True)
		self.detail_description.get_buffer().connect("changed", self.description_changed)
		scrolled.add(self.detail_description)
		self.fixed.pack_start(scrolled, False, False, 5)
		self.detail_btnaddparent = self.create_button(_("Add parents"), "images/addparent.svg", self.addparent_clicked)
		self.detail_btnaddbrother = self.create_button(_("Add brother/sister"), "images/addbrother.svg", self.addbrother_clicked)
		self.detail_btnaddunion = self.create_button(_("Add union"), "images/addunion.svg", self.addunion_clicked)
		self.detail_btnaddchild = self.create_button(_("Add child"), "images/addchild.svg", self.addchild_clicked)
		self.detail_btndelete = self.create_button(_("Delete"), "images/delete.svg", self.delete_clicked)
		self.fixed.pack_start(self.detail_btnaddparent, False, False, 2)
		self.fixed.pack_start(self.detail_btnaddunion, False, False, 2)
		self.fixed.pack_start(self.detail_btnaddbrother, False, False, 2)
		self.fixed.pack_start(self.detail_btnaddchild, False, False, 2)
		self.fixed.pack_start(self.detail_btndelete, False, False, 0)
		self.box = gtk.HBox(False)
		self.box.pack_start(self.fixed, True, True, 0)
		self.box.pack_start(self.area, True, True, 0)
		self.set_canvas(self.box)

		# Create empty tree
		self.tree = None
		self.selected = None
		self.init_tree(empty_tree(buddyName))
		
		# Show all
		self.show_all()
		self.area.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))
		
	
	def create_button(self, label, image, callback):
		"Create a bitmap button"
		button = gtk.Button()
		btncontainer = gtk.HBox()
		btnimage = gtk.Image()
		btnimage.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(image))
		btncontainer.pack_start(btnimage, False, False, 2)
		btncontainer.pack_start(gtk.Label(label), False, False, 10)
		button.add(btncontainer)
		button.connect("clicked", callback)
		
		return button
		
		
	def init_tree(self, tree):
		"Create and init a tree"
		self.zoomlevel = 0
		self.tree = tree
		(self.initx, self.inity) = (const.tree_initx, const.tree_inity)
		self.tree.set_position(self.initx, self.inity)
		self.show_detail(None)
		self.redraw()

		
	def set_center(self, person):
		"Set the center of the draw on a person"
		rect = self.area.allocation
		dx = (rect.width/2) - self.tree.root.x0 - (person.x0 - self.tree.root.x0) - (person.x1 - person.x0)/2
		dy = (rect.height/2) - self.tree.root.y0 - (person.y0 - self.tree.root.y0) - (person.y1 - person.y0)/2
		self.translate(dx, dy)
		
	
	def show_detail(self, person):
		"Show detail information for a person"
		
		# Change selection
		if self.selected is not None:
			self.selected.isselected = False
		self.selected = person
		
		
		# No selection
		if person == None:
			self.detail_name.set_sensitive(False)
			self.detail_description.set_sensitive(False)
			self.detail_name.set_text("")
			self.detail_description.get_buffer().set_text("")
			self.detail_chkmale.set_active(True)
			self.detail_chkmale.set_sensitive(False)
			self.detail_chkfemale.set_sensitive(False)
			self.detail_btnaddparent.set_sensitive(False)
			self.detail_btnaddbrother.set_sensitive(False)
			self.detail_btnaddunion.set_sensitive(False)
			self.detail_btnaddchild.set_sensitive(False)
			self.detail_btndelete.set_sensitive(False)
			return
			
		# A node is selected
		person.isselected = True
		self.detail_name.set_sensitive(True)
		self.detail_name.grab_focus()
		self.detail_description.set_sensitive(True)
		self.detail_description.get_buffer().set_text(person.description)
		self.detail_name.set_text(person.name)
		if person.sex == 'M':
			self.detail_chkmale.set_active(True)
		else:
			self.detail_chkfemale.set_active(True)
		
		# Compute button status
		checkable = (len(person.unions) == 0)
		self.detail_chkmale.set_sensitive(checkable)
		self.detail_chkfemale.set_sensitive(checkable)
		self.detail_btnaddchild.set_sensitive(len(person.unions) > 0)
		unionscount = len(person.unions)
		childcount = person.child_count()
		isfamily = self.tree.is_family(person)
		isdescendant = self.tree.is_descendant(person)
		isascendant = self.tree.is_ascendant(person)
		isroot = (self.tree.root == person)
		if person == self.tree.root:
			deletable = False
		elif unionscount == 0:
			deletable = True
		elif unionscount > 1:
			deletable = False
		elif unionscount == 1 and isdescendant:
			deletable = False
		elif childcount > 0:
			if isascendant  and (person.parents is None) and (childcount == 1):
				deletable = True
			else:
				deletable = False
		else:
			deletable = True
		self.detail_btndelete.set_sensitive(deletable)
		self.detail_btnaddunion.set_sensitive(isfamily)
		self.detail_btnaddparent.set_sensitive(person.parents is None and (isascendant or isroot))
		self.detail_btnaddbrother.set_sensitive(person.parents is not None)
		
		
	def area_expose_cb(self, area, event):
		"Draw tree event"
		
		# Create context then draw tree inside
		gc = self.area.window.cairo_create()
		pc = self.create_pango_context()
		self.tree.draw(gc, pc)
		gc.stroke()	

		
	def press_button(self, widget, event):
		"Mouse button clicked, detail a person or start the moving mode"
		
		# Look if click in a person
		p = self.tree.person_at(event.x, event.y)
		if p is not None:
			self.set_center(p)
			self.show_detail(p)
			self.moving = False
			return
		
		# Not found, pass in moving mode
		self.show_detail(None)
		self.movingStart = (event.x, event.y)
		self.moving = True
		self.area.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
				
	
	def translate(self, dx, dy):
		# Translate all the tree from deltax, deltay
		(self.initx, self.inity) = (self.initx+dx, self.inity+dy)
		self.tree.translate(dx, dy)
		self.redraw()
		
				
	def mouse_move(self, widget, event):
		"Mouse move event, in moving mode translate draw if in moving mode else change cursor on person"
		
		# In moving mode ?
		if self.moving:
			# Compute translation
			self.translate(event.x-self.movingStart[0], event.y-self.movingStart[1])
			self.movingStart = (event.x, event.y)
		
		else:
			# Look if a person is under the cursor
			p = self.tree.person_at(event.x, event.y)
			if p is not None:
				# Found one, change cursor
				self.area.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND1))
				return
				
			# Not found, set standard cursor
			self.area.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))
			
		
	def release_button(self, widget, event):
		"Mouse button released, stop moving mode"
		
		self.area.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))
		self.moving = False

		
	def zoom_in(self, event):
		"ToolBar button zoom in clicked"
		self.zoomlevel = self.zoomlevel + 1
		self.tree.scale(20)
		self.redraw()
		
		
	def zoom_out(self, event):
		"ToolBar button zoom out clicked"
		if self.zoomlevel == -3:
			return
		self.zoomlevel = self.zoomlevel - 1
		self.tree.scale(-20)
		self.redraw()
		
		
	def detail_changed(self, event):
		"Textfield for the detail has changed, change the matching person name"
		if self.selected == None:
			self.redraw()
			return
		self.selected.name = self.detail_name.get_text()
		self.redraw()
		
		
	def description_changed(self, event):		
		"Description has changed, change the matching person description"
		if self.selected == None:
			return
		buffer = self.detail_description.get_buffer()
		self.selected.description = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
	
	
	def sexradio_checked(self, widget, data):
		"Radio button for sex checked, change sex for the selected person"
		if self.selected is not None:
			self.selected.sex = data
		self.redraw()
		
	
	def addparent_clicked(self, event):
		"Add parent clicked"
		self.zoomlevel = 0
		(x, y) = (self.tree.root.x0, self.tree.root.y0)
		dad = self.tree.Person("", "M")
		mum = self.tree.Person("", "F")
		self.tree.Union(dad, mum).append_child(self.selected)
		self.tree.set_position(x, y)
		self.set_center(dad)
		self.show_detail(dad)
		self.redraw()
		
	
	def addbrother_clicked(self, event):
		"Add brother clicked"
		self.zoomlevel = 0
		newchild = self.tree.Person("", "M")
		self.selected.parents.append_child(newchild)
		self.tree.set_position(self.tree.root.x0, self.tree.root.y0)
		self.set_center(newchild)
		self.show_detail(newchild)
		self.redraw()
		
		
	def addchild_clicked(self, event):
		"Add child clicked"
		self.zoomlevel = 0
		newchild = self.tree.Person("", "M")
		self.selected.unions[0].append_child(newchild) # HACK: Child is add to the first union
		self.tree.set_position(self.tree.root.x0, self.tree.root.y0)
		self.set_center(newchild)
		self.show_detail(newchild)
		self.redraw()
		
		
	def addunion_clicked(self, event):
		"Add union clicked"
		self.zoomlevel = 0
		if self.selected.sex == "M":
			male = self.selected
			female = newunion = self.tree.Person("", "F")
		else:
			male = newunion = self.tree.Person("", "M")
			female = self.selected	
		self.tree.Union(male, female)
		self.tree.set_position(self.tree.root.x0, self.tree.root.y0)
		self.set_center(newunion)
		self.show_detail(newunion)
		self.redraw()
		

	def delete_clicked(self, event):
		"Delete button clicked"
		
		# Delete as union or person
		if self.tree.is_ascendant(self.selected)  and (self.selected.parents is None) and (self.selected.child_count() == 1):
			self.tree.remove_union(self.selected.unions[0])
		else:
			self.tree.remove(self.selected)

		# Recompute and redraw
		self.zoomlevel = 0
		self.tree.set_position(self.tree.root.x0, self.tree.root.y0)
		self.show_detail(None)
		
		
	def redraw(self):
		"Redraw area"
		self.area.queue_draw_area(0, 0, self.area.allocation.width, self.area.allocation.height)
		self.imagezone.queue_draw_area(0, 0, self.imagezone.allocation.width, self.imagezone.allocation.height)
		
		
	def image_expose(self, area, event):
		"Draw the image zone"
		gc = self.imagezone.window.cairo_create()
		pc = self.create_pango_context()
		
		# Draw border
		rect = self.imagezone.allocation
		gc.rectangle(0, 0, rect.width, rect.height)
		gc.set_source_rgb(*const.bg_color)
		gc.stroke()
		
		# Draw image
		if self.selected is None:
			image = self.image_hand1
		else:
			if self.selected.image is None:
				image = self.image_paste
			else:
				image = self.selected.image
		x = (rect.width - image.get_width())/2
		y = (rect.height - image.get_height())/2
		self.imagezone.window.draw_pixbuf(self.imagezone.window.new_gc(), image, 0, 0, x, y)
		
		# Draw text
		if self.selected is None or self.selected.image is None:
			if self.selected is None:
				text = _("Click a person to edit it")
			else:
				text = _("Click here to paste an image")
			layout = pango.Layout(pc)
			layout.set_text(text)
			layout.set_width(rect.width*pango.SCALE)
			layout.set_alignment(pango.ALIGN_CENTER)
			gc.set_source_rgb(0, 0, 0)
			gc.move_to(0, y + image.get_height())
			gc.show_layout(layout)	

		
	def image_release_button(self, widget, event):
		"Mouse button released on the image, drop image"
		
		if self.selected is None:
			return
				
		# Get image from clipboard
		clipboard = gtk.clipboard_get()
		image = None
		if clipboard.wait_is_image_available():
			image = clipboard.wait_for_image()
			
		# HACK: Get image from URIs list
		else:
			selection = clipboard.wait_for_contents('text/uri-list')
			if selection is None:
				return
			for uri in selection.get_uris():
				image = gtk.gdk.pixbuf_new_from_file(urlparse(uri).path)
				break
			if image is None:
				return

		# Match image to rectangle
		rect = self.imagezone.allocation
		image_width = image.get_width()
		image_height = image.get_height()
		if image_width > rect.width or image_height > rect.height:
			if image_width > image_height:
				target_width = rect.width
				target_height = (image_height * target_width) / image_width
			else:
				target_height = rect.height
				target_width = (image_width * target_height) / image_height
			image = image.scale_simple(target_width, target_height, gtk.gdk.INTERP_HYPER)
		self.selected.image = image
		self.redraw()
	
	
	def emptytree(self, event):
		"Init with an empty tree"
		self.init_tree(empty_tree(buddyName))
		
		
	def sample1(self, event):
		"Init with a sample tree"
		self.init_tree(sample_family1())

		
	def sample2(self, event):
		"Init with a sample tree"
		self.init_tree(sample_family2())
		
		
	def write_file(self, file_path):
		"Called when activity is saved, save the tree in the file"
		#self.metadata['current_page'] = '3'
		file = open(file_path, 'wb')
		try:
			self.tree.write_to(file)
		finally:
			file.close()		
		
	
	def read_file(self, file_path):
		"Called when activity is loaded, load the tree from the file"
		file = open(file_path, 'rb')
		try:
			tree = Tree().read_from(file)
		finally:
			file.close()
		self.init_tree(tree)		
		

			
# Dummy call to allow running on Windows
if not const.inSugar:
	RootsActivity(0)
	gtk.main()
