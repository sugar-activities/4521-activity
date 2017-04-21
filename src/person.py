from guid import Guid
import pango
import const


# Constants
const._person_width = 180
const._person_height = 72
const._person_wmargin_ratio = 18
const._person_hmargin_ratio = 4
const._male_color = (0, 0, 255)
const._female_color = (255, 0, 0)
const._selected_background = (255, 255, 255)
const._person_font = 'Arial'
const._person_fontsize = 7
const._normal_line_width = 2
const._root_line_width = 3


		
# Person class
class Person:
	"Class to represent a person in the tree"
	
	def __init__(self, name, sex, id=None):
		"Constructor: build"
		self.id = Guid().newid(id)
		self.name = name
		self.description = ""
		self.image = None
		if sex == 'M' or sex == 'm':
			self.sex = 'M'
		else:
			self.sex = 'F'
		self.parents = None
		self.unions = []
		(self.x0, self.y0, self.x1, self.y1, self.fontsize) = (None, None, None, None, const._person_fontsize)
		self.computed = False
		self.isroot = False
		self.isselected = False
		
		
	def width_margin(self):
		return const._person_width / const._person_wmargin_ratio
		
	
	def height_margin(self):
		return const._person_height / const._person_hmargin_ratio
		
		
	def append_union(self, union):
		"Add an union"
		self.unions.append(union)
	
	
	def tostring(self, level=1):
		"Translate to a formatted string, tree is horizontal"
		buf = "P"+str(self.id)+'\n'
		if self.unions == []:
			buf += '\t'*level + self.name + " " + self.sex
		else:
			for u in self.unions:
				if self.sex == 'M':
					opposite = u.mum
				else:
					opposite = u.dad
				buf += '\t'*level + self.name + " " + self.sex + '\n+' + '\t'*level + opposite.name + " " + opposite.sex + '\n'
				buf += u.tostring(level)
				
		return buf
		
		
	def size_desc(self):
		"Compute size to draw the person an its subtree"
		if self.unions == []:
			return 1
		totlen = 0
		for i, u in enumerate(self.unions):
			totlen = totlen + u.size_desc()
			if i != 0:
				totlen = totlen+self.unions[i-1].child_count()
		return totlen

	
	def point_inside(self, x, y):
		"Test if point is inside the drawing"
		return x >= self.x0 and x <= self.x1 and y >= self.y0 and y <= self.y1

		
	def child_count(self):
		"Compute number of childs"
		totchild = 0
		for u in self.unions:
			totchild = totchild + u.child_count()
		return totchild


	def level(self, count=0):
		"Compute number of level in the subtree of the person"
		childlevel = count
		for u in self.unions:
			for c in u.childs:
				childlevel = max(childlevel, c.level(count+1))
		return childlevel
		
			
	def set_pos(self, x, y):
		"Set person position"
		
		# Already done
		if self.computed:
			return
			
		# Set person position
		(self.x0, self.y0) = (x, y)
		(self.x1, self.y1) = (x+const._person_width, y+const._person_height)
		self.computed = True
		self.fontsize = const._person_fontsize
		
		
	def compute_desc_pos(self, x, y):
		"Compute person and its subtree draw starting at origin"
		
		if self.unions != []:
			# Set union position
			for i, u in enumerate(self.unions):
				# Next union
				if i != 0:
					size = u.size_desc()+self.unions[i-1].child_count()
					x = x + (size*const._person_width+size*self.width_margin())/2
				
				# Set conjoint position
				if self.sex == 'M':
					opposite = u.mum
				else:
					opposite = u.dad
				opposite.set_pos(x + const._person_width+self.width_margin(), y)
				
				# Set the union and childs of this union
				u.compute_desc_pos(x+const._person_width+(self.width_margin()/2), y+const._person_height+self.height_margin())
				
				# Shift right
				size = u.size_desc()
				x = x + (size*const._person_width+size*self.width_margin())/2
		
		
	def translate(self, dx, dy):
		"Translate coordinate"
		if self.x0 is None:
			return
		self.x0 = self.x0 + dx
		self.y0 = self.y0 + dy
		self.x1 = self.x1 + dx
		self.y1 = self.y1 + dy
		
	
	def scale(self, scalerate):
		"Scale coordinate and font"
		if self.x0 is None:
			return
		self.x0 = self.x0 + ((self.x0 * scalerate) / 100)
		self.y0 = self.y0 + ((self.y0 * scalerate) / 100)
		self.x1 = self.x1 + ((self.x1 * scalerate) / 100)
		self.y1 = self.y1 + ((self.y1 * scalerate) / 100)
		self.fontsize = self.fontsize + (scalerate / 10) 

		
	def draw(self, gc, pc):
		"Draw a person"
		
		# Do not draw person without coordinate
		if self.x0 is None:
			return
		
		# draw background for selected none
		if self.isselected:
			gc.rectangle(self.x0, self.y0, self.x1-self.x0, self.y1-self.y0)
			gc.set_source_rgb(*const._selected_background)
			gc.fill()
			gc.stroke()
			
		# draw border
		if self.sex == 'M':
			gc.set_source_rgb(*const._male_color)
		else:
			gc.set_source_rgb(*const._female_color)
		if self.isroot:
			gc.set_line_width(const._root_line_width)
		else:
			gc.set_line_width(const._normal_line_width)
		gc.rectangle(self.x0, self.y0, self.x1-self.x0, self.y1-self.y0)
		gc.stroke()
		
		# draw text
		layout = pango.Layout(pc)
		layout.set_width(int(self.x1-self.x0)*pango.SCALE)
		layout.set_text(self.name)
		layout.set_alignment(pango.ALIGN_CENTER)
		layout.set_wrap(pango.WRAP_WORD)
		layout.set_font_description(pango.FontDescription(const._person_font + " " + str(self.fontsize)))
		gc.move_to(self.x0, self.y0)
		gc.show_layout(layout)		
