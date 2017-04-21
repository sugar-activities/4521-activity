# Guid class		
class Guid:
	"Class used to generate unique identifier"
	
	class __impl:
		"Singleton class"
		def __init__(self):
			"Constructor, init reference count"
			self.count=0
		
		def newid(self, start=None):
			"Generate a new id"
			if start is None:
				self.count = self.count+1
			else:
				if self.count < start:
					self.count = start
				return start
			return self.count
		
	__instance=None
	
	def __init__(self):
		"Constructor, create Singleton if don't exist"
		if Guid.__instance is None:
			Guid.__instance = Guid.__impl()
		
		self.__dict__['_Guid__instance'] = Guid.__instance
		
	def __getattr__(self, attr):
		"Pass attr retrieving to Singleton"
		return getattr(self.__instance, attr)