import os, xbmc

class AutoexecHandler:
    #caller=id of the calling addon
    def __init__(self):
        self.file = xbmc.translatePath("special://profile/autoexec.py")
    
    def __getPath(self, id, library):
        return xbmc.translatePath("special://home/addons/" + id + "/" + library)
    
    def __getString(self, id, library):
        return "xbmc.executescript(\"" + self.__getPath(id, library) + "\")"
    
    #id=id of the owner addon, library=python file
    #wont add anything if the entry already exists
    def add(self, id, library):
        entry = self.__getString(id, library)
        imported = False
        
        file = open(self.file, 'r+')
        for line in file:
            if entry in line:
                return
            elif "import xbmc" in line:
                imported = True
        
        file.write("\n")
        if not imported:
            file.write("import xbmc\n")
        file.write(entry)
        file.write("\n")
        file.close()
    
    #id=id of the owner addon, library=python file
    def remove(self, id, library):
        if not(os.path.exists(self.file)):
            return
        
        entry = self.__getString(id, library)
        found = False
        out = []
        
        file = open(self.file, 'r')
        for line in file:
            if entry in line:
                found = True
            else:
                out.append(line)
        file.close()
        
        if not found:
            return
        
        file = open(self.file, 'w')
        file.writelines(out)
        file.close()
