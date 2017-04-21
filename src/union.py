from guid import Guid
import const


# Constants
const._union_color = (0, 0, 0)


# Union class
class Union:
	"Class to process union between two persons"
	
	def __init__(self, dad, mum, id=None):
		"Constructor, init dad, mum and childs"
		self.id = Guid().newid(id)
		self.dad = dad
		dad.append_union(self)
		self.mum = mum
		mum.append_union(self)
		self.childs = []
	
	
	def append_child(self, child):
		"Append a child born from the union"
		self.childs.append(child)
		child.parents = self
		
		
	def tostring(self, level=1):
		"Translate to a formatted string, tree is horizontal"	
		str = "U"+str(self.id)+"\n"
		for c in self.childs:
			str += c.tostring(level+1) + '\n'
			
		return str
		
		
	def size_desc(self):
		"Compute size to draw the union an its subtree"
		totlen = 0
		if self.childs == []:
			return 2
		for c in self.childs:
			totlen = totlen + c.size_desc()
		return max(2,totlen)	
		
	
	def compute_desc_pos(self, x, y):
		"Compute union subtree position"

		# Reinit size
		self.dad.fontsize = const._person_fontsize
		self.mum.fontsize = const._person_fontsize
		
		# Compute childs size
		size = 0
		for c in self.childs:
			size = size + c.size_desc()
		
		# Compute origin
		if len(self.childs) == 1:
			x = x - (const._person_width)/2
		else:
			x = x - (size*const._person_width+(size-1)*self.dad.width_margin())/2
		
		# Compute draw for childs
		for c in self.childs:
			c.set_pos(x, y)
			c.compute_desc_pos(x, y)
			size = c.size_desc()
			x = x + (size*const._person_width+size*c.width_margin())
	

	def conjoint(self, p):
		"Return conjoint"
		if p == self.dad:
			return self.mum
		else:
			return self.dad
			
		
	def child_count(self):
		"Compute number of childs"
		return len(self.childs)
		
		
	def draw(self, gc, pc):
		"Draw person and its subtree in the graphical context"
		
		# Do not draw person without coordinate
		if self.dad.x0 is None or self.mum.x0 is None:
			return
			
		# Draw link between parents
		if self.dad.x0 < self.mum.x0:
			(left, right) = (self.dad, self.mum)
		else:
			(left, right) = (self.mum, self.dad)
		if len(left.unions) > 1 and self != left.unions[0]:
			i = 1
			while left.unions[i].conjoint(left) != right:
				i = i + 1
			left = left.unions[i-1].conjoint(left)
		width = left.x1 - left.x0
		height = left.y1 - left.y0
		gc.move_to(left.x0+width, left.y0+(height/2))
		gc.line_to(right.x0, right.y0+(height/2))
		gc.set_source_rgb(*const._union_color)
		gc.stroke()
		
		# Draw link to child
		size = len(self.childs)
		for c in self.childs:
			# Draw link to child	
			if c.x0 is None:
				continue
			gc.move_to(right.x0-(c.width_margin()/2), right.y0+(height/2))
			gc.line_to(right.x0-(c.width_margin()/2), right.y0+height+(c.height_margin()/2))
			gc.line_to(c.x0+(width/2), right.y0+height+(c.height_margin()/2))
			gc.line_to(c.x0+(width/2), c.y0)
			gc.set_source_rgb(*const._union_color)
			gc.stroke()