# How to Install

---

### Copy files    
 * collectFiles.py
 * sweetberry.png    

into your .nuke folder.    

---

### Open your menu.py file, and type this:

```python
# CollectFiles  ////////////////////////////////////////////////////////////////////////////////////////

import collectFiles

#get main toolbar
toolbar = nuke.toolbar("Nodes")

#get 'Sweetberry' menu
ssMenu = toolbar.addMenu("Sweetberry", icon="sweetberry.png")

ssMenu.addCommand('CollectFiles','collectFiles.main()')
ssMenu.addCommand('AbsPath >> RelPath','collectFiles.absToRel()')
ssMenu.addCommand('RelPath >> AbsPath','collectFiles.relToAbs()')


#/////////////////////////////////////////////////////////////////////////////////////////////////////////////
```

---

### restart nuke.

# enjoy!.
