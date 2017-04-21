#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Base import
import pickle
import tempfile
import os
import gtk
from gettext import gettext as _

# Local import
from person import Person
from union import Union
import const


# Constants
const._buffer_size = 4096




# Tree class
class Tree:
	"Class to represent a tree: a sum of persons and unions"

	def __init__(self):
		"Constructor, init fields to None"
		self.root = None
		self.persons = []
		self.unions = []
	
	
	def read_from(self, file):
		"Read tree from the file"
		
		# Load persons
		count = pickle.load(file)
		for i in range(count):
			id = pickle.load(file)
			name = pickle.load(file)
			sex = pickle.load(file)
			description = pickle.load(file)
			image = self.load_image(file)
			p = self.Person(name, sex, id)
			p.description = description
			p.image = image
			
			
		# Load unions
		count = pickle.load(file)
		for i in range(count):		
			# Create union
			id = pickle.load(file)
			dadid = pickle.load(file)
			mumid = pickle.load(file)
			dad = self.get_person(dadid)
			if dad is None:
				_logger.debug("ERROR on "+str(dadid))
			mum = self.get_person(mumid)
			if mum is None:
				_logger.debug("ERROR on "+str(mumid))
			u = self.Union(dad, mum, id)
			
			# Create childs
			childcount = pickle.load(file)
			for j in range(childcount):
				childid = pickle.load(file)
				child = self.get_person(childid)
				if child is None:
					_logger.debug("ERROR on "+str(childid))
				u.append_child(child)
			
		# Get root
		rootid = pickle.load(file)
		root = self.get_person(rootid)
		if root is None:
			_logger.debug("ERROR on "+str(rootid))
		self.root = root
		root.isroot = True
		
		return self
		
		
	def write_to(self, file):
		"Write tree to file"
		
		# Save persons
		pickle.dump(len(self.persons), file)
		for p in self.persons:
			pickle.dump(p.id, file)
			pickle.dump(p.name, file)
			pickle.dump(p.sex, file)
			pickle.dump(p.description, file)
			self.dump_image(p.image, file)
		
		# Save unions
		pickle.dump(len(self.unions), file)
		for u in self.unions:
			pickle.dump(u.id, file)
			pickle.dump(u.dad.id, file)
			pickle.dump(u.mum.id, file)
			pickle.dump(len(u.childs), file)
			for c in u.childs:
				pickle.dump(c.id, file)
		
		# Save root
		pickle.dump(self.root.id, file)
		
		
	def dump_image(self, image, file):
		"Dump image into file"
		
		# Write if an image exist
		hasimage = image is not None
		pickle.dump(hasimage, file)
		if not hasimage:
			return
			
		# Save image to a temp file
		name = tempfile.mktemp()
		image.save(name, "png")
		fd = open(name, "rb")
		fd.seek(0, os.SEEK_END)
		size = fd.tell()
		fd.seek(0, os.SEEK_SET)
		
		# Write temp file content into the stream
		pickle.dump(size, file)
		while 1:
			buffer = fd.read(const._buffer_size)
			if not buffer:
				break
			file.write(buffer)
		fd.close()
		
		
	def load_image(self, file):
		"Load image from file"
		hasimage = pickle.load(file)
		if not hasimage:
			return None
			
		# Save file content to a temp file
		size = pickle.load(file)
		name = tempfile.mktemp()+".png"
		fd = open(name, "wb")
		current = size
		while 1:
			bufsize = min(const._buffer_size, current)
			buffer = file.read(bufsize)
			fd.write(buffer)
			current = current - const._buffer_size
			if current <= 0:
				break
		fd.close()
		
		# Create image from the temp file
		return gtk.gdk.pixbuf_new_from_file(name)
	
	
	def Person(self, name, sex, id=None):
		"Add a new person"
		p = Person(name, sex, id)
		self.persons.append(p)
		return p
		
	
	def Union(self, dad, mum, id=None):
		"Add a new union"
		u = Union(dad, mum, id)
		self.unions.append(u)
		return u
		
	
	def get_person(self, id):
		"Look for a person with an id"
		for p in self.persons:
			if p.id == id:
				return p
		return None
		
	
	def get_union(self, id):
		"Look for an union with an id"
		for u in self.unions:
			if u.id == id:
				return u
		return None		
		
		
	def is_descendant(self, person, root=None):
		"Look if person is a descendant of the tree"
		start = root
		if start is None:
			start = self.root
		for u in start.unions:
			for c in u.childs:
				if c == person:
					return True
				if self.is_descendant(person, c):
					return True
		return False
		
		
	def is_ascendant(self, person, root=None):
		"Look if person is an ascendant of the tree"
		start = root
		if start is None:
			start = self.root
		if start.parents is not None:
			if start.parents.dad == person or start.parents.mum == person:
				return True
			if self.is_ascendant(person, start.parents.dad):
				return True
			if self.is_ascendant(person, start.parents.mum):
				return True
		return False
		

	def is_family(self, person, root=None):
		"Look if person is a direct family member"
		
		# Start point
		start = root
		if start is None:
			start = self.root
			
		# Test 
		if start == person:
			return True
		if self.is_descendant(person, start):
			return True
					
		# Test parents
		if start.parents is not None:
			if self.is_family(person, start.parents.dad):
				return True
			if self.is_family(person, start.parents.mum):
				return True
				
		return False	
		
		
	def set_position(self, initx, inity):
		"Set the tree to this position"
		
		# Compute levels
		levels = dict()
		maxlevel = -1
		for p in self.persons:
			levelvalue = p.level()
			maxlevel = max(levelvalue, maxlevel)
			if levelvalue not in levels:
				levels[levelvalue] = []
			levels[levelvalue].append(p)
			p.computed = False
			
		# Set pos start starting on higher level
		(x, y) = (initx, inity)
		for levelvalue in reversed(range(maxlevel+1)):
			roots = levels[levelvalue]
			for i, root in enumerate(roots):
				root.set_pos(x, y)
				root.compute_desc_pos(x, y)
				size = root.size_desc()
				if i > 0:
					size = size + roots[i].child_count()
				x = x + (size*const._person_width+size*root.width_margin())/2
			x = initx
			y = y + const._person_height+root.height_margin()
		
	
	def draw(self, gc, pc):
		"Draw the tree in the graphical and pango context"
		for p in self.persons:
			p.draw(gc, pc)
			
		for u in self.unions:
			u.draw(gc, pc)
	
	
	def person_at(self, x, y):
		"Look for a person at this position"
		for p in self.persons:
			if p.point_inside(x, y):
				return p
		return None
		
	
	def translate(self, dx, dy):
		"Translate tree"
		for p in self.persons:
			p.translate(dx, dy)
		
		
	def scale(self, scalelevel):
		"Scale tree"
		for p in self.persons:
			p.scale(scalelevel)
			
	
	def remove(self, person):
		"Remove a person from the tree"
		# Remove from union
		for u in person.unions:
			self.unions.remove(u)
			if u.dad == person:
				u.mum.unions.remove(u)
			else:
				u.dad.unions.remove(u)

		# Remove from parent child
		if person.parents is not None:
			person.parents.childs.remove(person)
			
		# Remove from tree
		self.persons.remove(person)
		
		
	def remove_union(self, union):
		"Remove an union from the tree"
		# Remove from child
		for c in union.childs:
			c.parents = None
		
		# Remove from parent
		union.dad.unions.remove(union)
		union.mum.unions.remove(union)
		
		# Remove from tree
		self.unions.remove(union)
		
		# Remove dad and mum
		self.remove(union.dad)
		self.remove(union.mum)
			

# Create the samples family		
def empty_tree(xoOwner):
	tree = Tree()
	tree.root = tree.Person(xoOwner, "M")
	tree.root.isroot = True
	
	return tree
	
	
def sample_family1():
	# Large family sample
	tree = Tree()	
	
	l = tree.Person("Lucien", "M")
	a = tree.Person("Annick", "F")
	u = tree.Union(l, a)

	d = tree.Person("Dominique", "M")
	u.append_child(d)
	au = tree.Person("Anne", "F")
	u.append_child(au)
	m = tree.Person("Madeleine", "F")
	u.append_child(m)

	jp = tree.Person("Jean-Pierre", "M")
	j = tree.Person("Julie", "F")
	up = tree.Union(jp, j)
	up.append_child(l)
	c = tree.Person("Christian", "M")
	up.append_child(c)
	
	jo = tree.Person("Jonathan", "M")
	ub = tree.Union(jo, j)
	ub.append_child(tree.Person("Charlie", "F"))
	
	rs = tree.Person("Renée", "F")
	vm = tree.Person("Vivien", "M")
	urv = tree.Union(vm, rs)
	urv.append_child(j)

	jr = tree.Person("Jean-René", "M")
	ua = tree.Union(jr, tree.Person("Micheline", "F"))
	ua.append_child(a)
	i = tree.Person("Irène", "F")
	ua.append_child(i)
	ui = tree.Union(tree.Person("Nathan", "M"), i)
	ui.append_child(tree.Person("Marie", "F"))
	ui.append_child(tree.Person("Noël", "M"))
	ui.append_child(tree.Person("Thierry", "M"))

	uc = tree.Union(c, tree.Person("Clarah", "F"))
	sa = tree.Person("Sandrine", "F")
	uc.append_child(sa)
	uc2 = tree.Union(c, tree.Person("Vivianne", "F"))
	pi = tree.Person("Pierre", "M")
	uc2.append_child(pi)
	uc2.append_child(tree.Person("Camille", "F"))
	
	tree.root = d
	tree.root.isroot = True
	
	return tree
	
	
def sample_family2():
	# Napoleon family
	tree = Tree()	
	tree.root = p1 = tree.Person("Charles-Marie Bonaparte", "M")
	p1.description = _("(1746-1785) This young Corsican aristocrat studied law in Italy and Corsica.")
	p1.image = gtk.gdk.pixbuf_new_from_file("images/napo_p1.jpg")
	p2 = tree.Person("Letizia Ramolino", "F")
	p2.description = _("(1750-1836) She married very young, at 14 years old. In Corsica, she was known as the 'little marvel', famed for her beauty far and wide.")
	p2.image = gtk.gdk.pixbuf_new_from_file("images/napo_p2.jpg")
	u1 = tree.Union(p2, p1)
	p4 = tree.Person("Napoléon Ier", "M")
	p4.description = _("(1769-1821) He was born on 15 August 1769 in Ajaccio, Corsica. At the age of 10, he left Corsica with his older brother Joseph to study at the Ecole Militaire in Paris.")
	p4.image = gtk.gdk.pixbuf_new_from_file("images/napo_p4.jpg")
	p6 = tree.Person("Louis Bonaparte", "M")
	p6.description = _("(1778-1846) While still a child, Louis joined his brother Napoleon in Paris. He accompanied his brother on his early military campaigns and became King of Holland at the age of 28.")
	p6.image = gtk.gdk.pixbuf_new_from_file("images/napo_p6.jpg")
	u1.append_child(p4)
	u1.append_child(p6)
	p3 = tree.Person("Joséphine", "F")
	p3.description = _("(1763-1814) She was born in Martinique and arrived in Paris at the age of 16. Her first hushband Alexandre de Beauharnais was guillotined during the French Revolution.")
	p3.image = gtk.gdk.pixbuf_new_from_file("images/napo_p3.jpg")
	u2 = tree.Union(p4, p3)
	p5 = tree.Person("Marie-Louise d'Autriche", "F")
	p5.description = _("(1791-1847) She was daughter of the king of Austria and became Napoleon's second wife.")
	p5.image = gtk.gdk.pixbuf_new_from_file("images/napo_p5.jpg")
	u3 = tree.Union(p4, p5)
	
	p10 = tree.Person("Napoléon II", "M")
	p10.description = _("(1811-1832) When the French Empire fell once and for all, he followed his mother to Austria and died at a very young age, only 21 years old.")
	p10.image = gtk.gdk.pixbuf_new_from_file("images/napo_p10.jpg")
	u3.append_child(p10)
	
	p7 = tree.Person("Hortense de Beauharnais", "F")
	p7.description = _("(1783-1837) She had a gift for music and wrote and composed romantic songs. She married Louis and became Queen of Holland.")
	p7.image = gtk.gdk.pixbuf_new_from_file("images/napo_p7.jpg")
	u4 = tree.Union(p6, p7)
	p8 = tree.Person("Napoléon III", "M")
	p8.description = _("(1808-1873) He had to spend a large part of his childhood in Switzerland with his mother. He became officer then president in 1848.")
	p8.image = gtk.gdk.pixbuf_new_from_file("images/napo_p8.jpg")
	u4.append_child(p8)
	
	p9 = tree.Person("Eugenie de Palafox-Guzman", "F")
	p9.description = _("(1826-1920) Daughter of a Spanish count, she became Empress through her marriage in 1853.")
	p9.image = gtk.gdk.pixbuf_new_from_file("images/napo_p9.jpg")
	u5 = tree.Union(p8, p9)
	p11 = tree.Person("Louis Napoléon", "M")
	p11.description = _("(1856-1879) When the French army was beaten by the Prussian army, he had to leave France. He chose to become a soldier for the English and was killed in South Africa.")
	p11.image = gtk.gdk.pixbuf_new_from_file("images/napo_p11.jpg")
	u5.append_child(p11)
	
	tree.root.isroot = True
	
	return tree	

