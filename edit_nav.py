from collections import deque
from math import ceil, floor

from cudatext import *

from time import time # dbg

"""
on every on_change() check number of lines
  if line count changed:  get lines-per-caret
    for 'edited_lines': for each caret: move each line and caret pos after it by lines-per-caret

* TEST: 
  multicaret multiline paste before and after edited line + Undo
  several new lines before edit, + several deletes
"""

dqlen = 30
merge_adjacent_edits = True

class Command:
    
    def __init__(self):
        self.edited_lines = {} # filename:deque of line indexes
        self.deque_inds = dict() # filename:current index in deque of edited line indexes 
        self.last_carets = deque([None, None], 2)
        
        self.line_counts = {} # filename:last line count


    def to_last_edit(self):  # menu item, for keyboard shortcut 
      f = ed.get_filename()
        
      if f in self.edited_lines:
        ind = self.deque_inds.setdefault(f, 0)
        
        if ind < len(self.edited_lines[f]): 
          target_line = self.edited_lines[f][ind]
          ed.set_caret(0, target_line) 
          self.deque_inds[f] += 1
          
          
    def on_change(self, ed_self):
      shifted = self.shift_lines(ed_self)
      
      self.save_edit_pos(ed_self)      

      #if shifted:
        #f = ed_self.get_filename() 
        #print(f' == {self.edited_lines.get(f)}')
      
      
    def on_caret(self, ed_self):
      self.last_carets.appendleft(ed_self.get_carets())
      
      
    def shift_lines(self, ed_self):
      """if number of lines in file changed - shift saved edited lines accordingly
      """
      f = ed_self.get_filename() 
      lc = ed_self.get_line_count()
      last_lc = self.line_counts.setdefault(f, lc) # default is 'lc' - cant shift properly if dont know previous line count, so whatever

      if lc != last_lc:
        self.line_counts[f] = lc

        edited_lines = self.edited_lines.get(f) # deque
        if edited_lines:
          carets = self.last_carets[1]  # 0 is current, 1 is previous
          if carets == None: # should_never_happen_tm
            return
            
          caret_count = len(carets)
          lines_delta = lc - last_lc
          # cant delete last line OR backspace first => might not be integer, thus ceil() and floor()
          lines_per_caret = ceil(lines_delta / caret_count)  if lines_delta > 0 else  floor(lines_delta / caret_count) 
          #print(f'line count: {last_lc} => {lc} (carn:{caret_count}, dt:{lines_delta}) [crt:{carets} => {self.last_carets[1]} ({time()}')
        
          for ci in range(len(carets)): # array values are modified in loop => range() just in case
            carety = carets[ci][1]
            for i,line in enumerate(edited_lines):
              # shift lines after current caret
              if line >= carety: 
                edited_lines[i] = line + lines_per_caret  
                #print(f'  moved: line[{i}]:{line}  (caret[{ci}]:{carety})  =>  {edited_lines[i]}')
            
            # shift carets after current one (along with lines)
            if caret_count - (ci+1) > 0:
              #print(f'    -- shifting carets: {carets}')
              carets[ci+1:caret_count] = [(x,y+lines_per_caret,a,b) for (x,y,a,b) in carets[ci+1:caret_count]]
              #print(f'                     => {carets}')
                
          #print(f' - fixed edits: {edited_lines}')
          return True # shifted
          
          
    def save_edit_pos(self, ed_self):
      line = ed_self.get_carets()[0][1] # y of first caret
      f = ed_self.get_filename() 
       
      if f not in self.edited_lines:
        self.edited_lines[f] = deque([0], dqlen) 

      self.deque_inds[f] = 0 # reset 
      ## store edited line index  (or move to start of deque)
      if line in self.edited_lines[f]:
        self.edited_lines[f].remove(line)
      
      if merge_adjacent_edits  and  abs(line - self.edited_lines[f][0]) == 1:
        self.edited_lines[f].popleft()
      
      self.edited_lines[f].appendleft(line) 
      
