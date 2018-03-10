# -*- coding: utf-8 -*-

from toolbox import *
from toolbox import _
from goban import *
import sys
from datetime import datetime
from tkinter import *
from threading import Lock
import leela_analysis,gnugo_analysis,ray_analysis,aq_analysis,leela_zero_analysis
import queue

import configparser

#bots_for_analysis=[leela_analysis.Leela,aq_analysis.AQ,ray_analysis.Ray,gnugo_analysis.GnuGo,leela_zero_analysis.LeelaZero]
bots_for_playing=[leela_analysis.Leela,aq_analysis.AQ,ray_analysis.Ray,gnugo_analysis.GnuGo,leela_zero_analysis.LeelaZero]

class LiveAnalysisLauncher(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.parent=parent
		self.popup=None
		root = self
		root.parent.title('GoReviewPartner')
		
		Config = configparser.ConfigParser()
		Config.read(config_file)
		
		self.pack(padx=10, pady=10)

		row=1
		value={"slow":" (%s)"%_("Slow profile"),"fast":" (%s)"%_("Fast profile")}
		self.analysis_bots_names=[bot['name']+value[bot['profile']] for bot in get_available("LiveAnalysisBot")]
		Label(self,text=_("Bot to use for analysis:")).grid(row=row,column=1,sticky=W)
		self.bot_selection=StringVar()	
		#apply(OptionMenu,(self,self.bot_selection)+tuple(self.analysis_bots_names)).grid(row=row,column=2,sticky=W)
		OptionMenu(self,self.bot_selection,*tuple(self.analysis_bots_names)).grid(row=row,column=2,sticky=W)
		
		self.bots_names=[bot['name']+value[bot['profile']] for bot in get_available("LivePlayerBot")]
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Black player")).grid(row=row,column=1,sticky=W)
		self.black_selection=StringVar()	
		self.black_selection_wrapper=Frame(self)
		self.black_selection_wrapper.grid(row=row,column=2,sticky=W)
		self.black_options=[_("Human"),_("Bot used for analysis")]+self.bots_names
		#self.black_menu=apply(OptionMenu,(self.black_selection_wrapper,self.black_selection)+tuple(self.black_options))
		self.black_menu=OptionMenu(self.black_selection_wrapper,self.black_selection,*tuple(self.black_options))
		self.black_menu.pack()

		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("White player")).grid(row=row,column=1,sticky=W)
		self.white_selection=StringVar()
		self.white_selection_wrapper=Frame(self)
		self.white_selection_wrapper.grid(row=row,column=2,sticky=W)
		self.white_options=[_("Human"),_("Bot used for analysis")]+self.bots_names
		#self.white_menu=apply(OptionMenu,(self.white_selection_wrapper,self.white_selection)+tuple(self.white_options))
		self.white_menu=OptionMenu(self.white_selection_wrapper,self.white_selection,*tuple(self.white_options))
		self.white_menu.pack()
		
		row+=1
		self.overlap_thinking_wrapper=Frame(self)
		self.overlap_thinking_wrapper.grid(row=row,column=1,columnspan=2,sticky=W)
		self.overlap_thinking_widgets=[]
		
		nooverlap=True
		try:
			nooverlap=Config.get("Live","NoOverlap")
		except:
			pass
		self.no_overlap_thinking = BooleanVar(value=nooverlap)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("Board size")).grid(row=row,column=1,sticky=W)
		self.dim=Entry(self)
		self.dim.grid(row=row,column=2,sticky=W)
		self.dim.delete(0, END)
		size="19"
		try:
			size=Config.get("Live", "size")
		except:
			Config.set("Live", size)
		self.dim.insert(0, size)

		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("Komi")).grid(row=row,column=1,sticky=W)
		self.komi=Entry(self)
		self.komi.grid(row=row,column=2,sticky=W)
		self.komi.delete(0, END)
		komi="7.5"
		try:
			komi=Config.get("Live", "komi")
		except:
			Config.set("Live", komi)
		self.komi.insert(0, komi)	

		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("Handicap stones")).grid(row=row,column=1,sticky=W)
		self.handicap=Entry(self)
		self.handicap.grid(row=row,column=2,sticky=W)
		self.handicap.delete(0, END)
		handicap="0"
		try:
			handicap=Config.get("Live", "handicap")
		except:
			Config.set("Live", handicap)
		self.handicap.insert(0, handicap)

		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("SGF file name")).grid(row=row,column=1,sticky=W)
		self.filename=Entry(self)
		self.filename.grid(row=row,column=2,sticky=W)
		self.filename.delete(0, END)
		filename=datetime.now().strftime('%Y-%m-%d_%H-%M_'+_('Human')+'_vs_'+_('Human')+'.sgf')
		self.filename.insert(0, filename)
		self.filename.bind("<Button-1>",self.change_filename)
		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1		
		Button(self,text=_("Start"),command=self.start).grid(row=row,column=2,sticky=E)

		self.bot_selection.set(self.analysis_bots_names[0])
		self.black_selection.set(_("Human"))
		self.white_selection.set(_("Human"))
		
		analyser=Config.get("Live","Analyser")
		if analyser in self.analysis_bots_names:
			self.bot_selection.set(analyser)
		
		self.change_parameters()
		
		black=Config.get("Live","black")
		if black in self.black_options:
			self.black_selection.set(black)
			
		white=Config.get("Live","white")
		if white in self.white_options:
			self.white_selection.set(white)
		
		self.bot_selection.trace("w", lambda a,b,c: self.change_parameters())
		self.black_selection.trace("w", lambda a,b,c: self.change_parameters())
		self.white_selection.trace("w", lambda a,b,c: self.change_parameters())
	
	def change_filename(self,event=None):
		filename=save_live_game(self.filename.get(), parent=self)
		if filename:
			filename=os.path.basename(filename)
			self.filename.delete(0, END)
			self.filename.insert(0, filename)
		
	def close_app(self):
		if self.popup:
			try:
				log("closing RunAlanlysis popup from RangeSelector")
				self.popup.close_app()
			except:
				log("RangeSelector could not close its RunAlanlysis popup")
				pass

	def start(self):
		#bots={bot['name']:bot for bot in bots_for_analysis}
		#analyser=bots[self.bot_selection.get()]
		value={"slow":" (%s)"%_("Slow profile"),"fast":" (%s)"%_("Fast profile")}
		bots={bot['name']+value[bot['profile']]:bot for bot in get_available("LiveAnalysisBot")}
		analyser=bots[self.bot_selection.get()]
		
		bots={bot['name']+value[bot['profile']]:bot for bot in get_available("LivePlayerBot")}
		
		b=self.selected_black_index()
		if b==0:
			black="human"
		elif b==1:
			black="analyser"
		else:
			print ("==========")
			print (bots.keys())
			print ("==========")
			black=bots[self.black_selection.get()]
		
		w=self.selected_white_index()
		if w==0:
			white="human"
		elif w==1:
			white="analyser"
		elif w==b:
			white="black"
		else:
			white=bots[self.white_selection.get()]
		
		Config = configparser.ConfigParser()
		Config.read(config_file)
		
		komi=float(self.komi.get())
		dim=int(self.dim.get())
		handicap=int(self.handicap.get())
		
		Config.set("Live","komi",str(komi))
		Config.set("Live","size",str(dim))
		Config.set("Live","handicap",str(handicap))
		
		Config.set("Live","analyser",self.bot_selection.get())#.encode("utf"))
		Config.set("Live","black",self.black_selection.get())#.encode("utf"))
		Config.set("Live","white",self.white_selection.get())#.encode("utf"))
		
		Config.write(open(config_file,"w",encoding='utf8'))
		 
		filename=os.path.join(Config.get("General","livefolder"),self.filename.get())
		
		self.popup=LiveAnalysis(self.parent.parent,analyser,black,white,dim=dim,komi=komi,handicap=handicap,filename=filename,overlap_thinking=not self.no_overlap_thinking.get())
		self.parent.destroy()

	def selected_black_index(self):
		i=0
		for bo in self.black_options:
			#if bo.decode("utf")==self.black_selection.get():
			if bo==self.black_selection.get():
				return i
			i+=1

	def selected_white_index(self):
		i=0
		for wo in self.white_options:
			#if wo.decode("utf")==self.white_selection.get():
			if wo==self.white_selection.get():
				return i
			i+=1

	def update_black_white_options(self):
		i=self.selected_black_index()
		self.black_options=[_("Human"),_("Bot used for analysis")+": "+self.bot_selection.get()]+self.bots_names
		self.black_menu.pack_forget()
		#self.black_menu=apply(OptionMenu,(self.black_selection_wrapper,self.black_selection)+tuple(self.black_options))
		self.black_menu=OptionMenu(self.black_selection_wrapper,self.black_selection,*tuple(self.black_options))
		self.black_menu.pack()
		self.black_selection.set(self.black_options[i])

		j=self.selected_white_index()
		self.white_options=[_("Human"),_("Bot used for analysis")+": "+self.bot_selection.get()]+self.bots_names
		self.white_menu.pack_forget()
		#self.white_menu=apply(OptionMenu,(self.white_selection_wrapper,self.white_selection)+tuple(self.white_options))
		self.white_menu=OptionMenu(self.white_selection_wrapper,self.white_selection,*tuple(self.white_options))
		self.white_menu.pack()
		self.white_selection.set(self.white_options[j])
		
		if i==1:
			black=self.bot_selection.get()
		else:
			black=self.black_selection.get()
			
		if j==1:
			white=self.bot_selection.get()
		else:
			white=self.white_selection.get()
			
		self.filename.delete(0, END)
		filename=datetime.now().strftime('%Y-%m-%d_%H-%M_'+black+'_vs_'+white+'.sgf')
		self.filename.insert(0, filename)

	def change_parameters(self):
		log("Bot selected for analysis is",self.bot_selection.get())
		self.update_black_white_options()
		self.update_overlap_thinking_option()
	
	def update_overlap_thinking_option(self):
		i=self.selected_black_index()
		j=self.selected_white_index()
		if i<=1 and j<=1:
			nb_bots=1
		elif (i>1 and j<=1) or (j>1 and i<=1):
			nb_bots=2
		elif (i>1 and j>1 and i==j):
			nb_bots=2
		elif (i>1 and j>1 and i!=j):
			nb_bots=3
		
		for widget in self.overlap_thinking_widgets:
				widget.grid_forget()
		self.overlap_thinking_widgets=[]
		
		if nb_bots>1:
			row=0
			widget=Label(self.overlap_thinking_wrapper,text="")
			widget.grid(row=row,column=1)
			self.overlap_thinking_widgets.append(widget)
			
			row+=1
			widget=Label(self.overlap_thinking_wrapper,text=_("No overlap thinking time"))
			widget.grid(row=row,column=1,sticky=W)
			self.overlap_thinking_widgets.append(widget)
			
			widget=Checkbutton(self.overlap_thinking_wrapper, text="", variable=self.no_overlap_thinking,onvalue=True,offvalue=False)
			widget.grid(row=row,column=2,sticky=W)
			self.overlap_thinking_widgets.append(widget)
			
class LiveAnalysis():
	def __init__(self,parent,analyser=None,black=None,white=None,dim=19,komi=6.5,handicap=0,filename="Live.sgf",overlap_thinking=False):
		self.parent=parent
		self.dim=dim
		self.komi=komi
		self.handicap=handicap
		self.filename=filename
		self.overlap_thinking=overlap_thinking
		
		self.analyser=analyser
		self.black=black
		self.white=white
		
		self.black_just_passed=False
		self.white_just_passed=False
		
		self.initialize()
		
	def initialize(self):
		Config = configparser.ConfigParser()
		Config.read(config_file)
		

		self.popup=Toplevel(self.parent)
		popup=self.popup
		
		dim=self.dim
		
		#popup.configure(background=bg)
		bg=popup.cget("background")
 
		panel=Frame(popup, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		
		panel.grid(column=1,row=1,sticky=N+S)
		
		display_factor=.5
		try:
			display_factor=float(Config.get("Review", "GobanScreenRatio"))
		except:
			Config.set("Review", "GobanScreenRatio",display_factor)
			Config.write(open(config_file,"w"))
		
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		
		self.goban_size=min(width,height)
		
		goban = Goban(dim,master=popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		goban.space=self.goban_size/(dim+1+1)
		goban.grid(column=2,row=1,rowspan=2,sticky=N+S+E+W)
		popup.grid_rowconfigure(1, weight=1)
		popup.grid_columnconfigure(2, weight=1)
		
		grid=[[0 for row in range(dim)] for col in range(dim)]
		markup=[["" for row in range(dim)] for col in range(dim)]
		
		
				
		self.goban=goban
		self.grid=grid
		self.markup=markup

		self.history=[]

		self.g = sgf.Sgf_game(size=self.dim)
		self.g.get_root().set("KM", self.komi)
		self.g_lock=Lock()
		self.g.lock=self.g_lock
		
		#self.analyser=self.analyser[0](self.g,self.filename)
		self.analyser=self.analyser["liveanalysis"](self.g,self.filename,self.analyser["profile"])
		
		self.cpu_lock=Lock()
		if not self.overlap_thinking:
			self.analyser.cpu_lock=self.cpu_lock #analyser and bot share the same cpu lock
		
		self.analyser.start()
			
		if type(self.black)!=type("abc"):
			#black is neither human nor analyser
			#so it's a bot
			log("Starting bot for black")
			#self.black=bot_starting_procedure(self.black[2],self.black[3],self.black[1],self.g,profil="fast")
			self.black=self.black["starting"](self.g,profile=self.black["profile"])
			log("Black bot started")
		
		if type(self.white)!=type("abc"):
			#white is neither human nor analyser not black
			#so it's a bot
			log("Starting bot for white")
			#self.white=bot_starting_procedure(self.white[2],self.white[3],self.white[1],self.g,profil="fast")
			self.white=self.white["starting"](self.g,profile=self.white["profile"])
			log("White bot started")
			
		goban.display(grid,markup)
		self.goban.bind("<Configure>",self.redraw)
		popup.focus()
		self.display_queue=queue.Queue(1)
		self.locked=False
		
		row=1
		Label(panel,text=_("Game"), font="-weight bold").grid(column=1,row=row,sticky=W)

		row+=1
		if self.black=="human":
			player_black=_("Human")
		elif self.black=="analyser":
			player_black=self.analyser.bot.bot_name
		else:
			player_black=self.black.bot_name
			
		self.game_label=Label(panel,text=_("Black")+": "+player_black)
		self.game_label.grid(column=1,row=row,sticky=W)
		
		
		row+=1
		if self.white=="human":
			player_white=_("Human")
		elif self.white=="analyser":
			player_white=self.analyser.bot.bot_name
		elif self.white=="black":
			player_white=player_black
		else:
			player_white=self.white.bot_name
			
		self.game_label=Label(panel,text=_("White")+": "+player_white)
		self.game_label.grid(column=1,row=row,sticky=W)

		row+=1
		self.game_label=Label(panel,text=_("Komi")+": "+str(self.komi))
		self.game_label.grid(column=1,row=row,sticky=W)

		row+=1
		self.game_label=Label(panel,text=_("Currently at move %i")%1)
		self.game_label.grid(column=1,row=row,sticky=W)
		
		
		row+=1
		self.pass_button=Button(panel,text=_("Pass"),state="disabled",command=self.player_pass)
		
		
		self.undo_button=Button(panel,text=_("Undo"),state="disabled")
		
		if (self.black=="human") or (self.white=="human"):
			self.pass_button.grid(column=1,row=row,sticky=W+E)
			self.undo_button.grid(column=1,row=row+1,sticky=W+E)
		row+=1
		if (self.black!="human") and (self.white!="human"):
			row+=1
			self.pause_button=Button(panel,text=_("Pause"),command=self.pause)
			self.pause_button.grid(column=1,row=row,sticky=W+E)
		self.pause_lock=Lock()
		
		row+=1
		Label(panel,text="").grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis"), font="-weight bold").grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis by %s")%self.analyser.bot.bot_name).grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis status:")).grid(column=1,row=row,sticky=W)
		
		row+=1
		self.analysis_label=Label(panel,text=_("Ready to start"))
		self.analysis_label.grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,fg=bg,text=_("Currently at move %i")%1000).grid(column=1,row=row,sticky=W) #yes, this is a ugly hack :)
		row+=1
		Label(panel,fg=bg,text=_("Waiting for next move")).grid(column=1,row=row,sticky=W) #yes, this is a ugly hack :)
		
		row+=1
		Label(panel,text="").grid(column=1,row=row,sticky=W)
		
		row+=1
		self.review_bouton_wrapper=Frame(panel)
		self.review_bouton_wrapper.grid(column=1,row=row,sticky=W+E)
		
		if self.handicap>0:
			self.handicap_stones=[]
			self.history.append(None)
			show_info(_("Place %i handicap stones on the board")%self.handicap,self.popup)
			goban.bind("<Button-1>",lambda e: self.place_handicap(e,self.handicap))
			
		else:
			self.next_color=1		
			self.current_move=1
			self.g.get_root().set("PL", "b")
			self.black_to_play()
			
		self.popup.protocol("WM_DELETE_WINDOW", self.close)
		self.parent.after(500,self.follow_analysis)
		
	def close(self):
		log("Closing analyser bot")
		self.game_label.config(text=_("Now closing, please wait"))
		self.analysis_label.config(text=_("Now closing, please wait"))
		log("Sending None msg to analyser")
		self.analyser.update_queue.put((0,None))
		if type(self.black)!=type("abc"):
			log("Closing black bot")
			self.black.close()
		if type(self.white)!=type("abc"):
			log("Closing white bot")
			self.white.close()
		
		self.analyser.bot.close()

		
		self.popup.destroy()
		
	def pause(self):
		if self.pause_button.cget("relief")!=SUNKEN:
			log("Pausing the game")
			self.pause_button.config(relief=SUNKEN)
			self.pause_button.config(text=_("Resume"))
			self.pause_lock.acquire()
			log("Game paused")
		else:
			log("Resuming the game")
			self.pause_button.config(relief=RAISED)
			self.pause_button.config(text=_("Pause"))
			self.pause_lock.release()
			log("Game resumed")
		
	def start_review(self):
		import dual_view
		
		app=self.parent
		screen_width = app.winfo_screenwidth()
		screen_height = app.winfo_screenheight()
		
		Config = configparser.ConfigParser()
		Config.read("config.ini")
		
		display_factor=.5
		try:
			display_factor=float(Config.get("Review", "GobanScreenRatio"))
		except:
			Config.set("Review", "GobanScreenRatio",display_factor)
			Config.write(open("config.ini","w"))
		
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		
		popup=Toplevel(self.parent)
		new_popup=dual_view.DualView(popup,self.filename[:-4]+".rsgf",min(width,height))
		new_popup.pack(fill=BOTH,expand=1)

	def follow_analysis(self):
		msg=None
		try:
			msg=self.analyser.label_queue.get(False)
			if type(msg)==type(123):
				self.analysis_label.config(text=_("Currently at move %i")%msg)

			else:
				self.analysis_label.config(text=_("Waiting for next move"))
				
			if msg>2 and len(self.review_bouton_wrapper.children)==0:
				Button(self.review_bouton_wrapper,text=_("Start review"),command=self.start_review).pack(fill=X)
			
		except:
			pass
		
		if msg==None:
			self.parent.after(500,self.follow_analysis)
		else:
			self.parent.after(10,self.follow_analysis)

	def place_handicap(self,event,handicap):
		dim=self.dim
		#add/remove black stone
		#check pointer location
		i,j=self.goban.xy2ij(event.x,event.y)
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			#inside the grid
			#what is under the pointer ?
			
			if self.grid[i][j] not in (1,2):
				self.analyser.bot.place(ij2gtp((i,j)),1)
				self.history[0]=[copy(self.grid),copy(self.markup)]
				place(self.grid,i,j,1)
				self.grid[i][j]=1
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
				self.goban.display(self.grid,self.markup)
				self.handicap_stones.append([i,j])
				#if type(self.black)!=type("abc"):
				#	self.black.place_black(ij2gtp((i,j)))
				#if type(self.white)!=type("abc"):
				#	self.white.place_black(ij2gtp((i,j)))
					
				if handicap>1:
					self.goban.bind("<Button-1>",lambda e: self.place_handicap(e,handicap-1))
				else:
					self.g.get_root().set("AB",self.handicap_stones)
					#write_sgf(self.filename,self.g.serialise())
					print (self.handicap_stones)
					if type(self.black)!=type("abc"):
						self.black.set_free_handicap([ij2gtp([i,j]) for i,j in self.handicap_stones])
					if type(self.white)!=type("abc"):
						self.white.set_free_handicap([ij2gtp([i,j]) for i,j in self.handicap_stones])
						
					show_info(_("The game is now starting"),self.popup)
					self.next_color=2
					#self.goban.bind("<Button-1>",self.click)
					
					self.g.get_root().set("PL", "w")
					
					self.current_move=1
					self.white_to_play()
	
	def gtp_thread_wrapper(self,bot,color):
		self.cpu_lock.acquire()
		if color=="black":
			answer=bot.play_black()
		else:
			answer=bot.play_white()
		threading.current_thread().answer=answer
		threading.current_thread().bot=bot
	
	def undo_as_black(self):
		log("Black undo from move",self.current_move,"back to move",self.current_move-2)
		self.undo_button.config(state='disabled')
		self.pass_button.config(state='disabled')
		self.goban.display(self.grid,self.markup,freeze=True)
		self.parent.after(100,self.undo)
		#self.undo()

	def undo_as_white(self):
		log("White undo from move",self.current_move,"back to move",self.current_move-2)
		self.undo_button.config(state='disabled')
		self.pass_button.config(state='disabled')
		self.goban.display(self.grid,self.markup,freeze=True)
		self.parent.after(100,self.undo)
		#self.undo()
		
	def undo(self):
		log("Let's wait for the analyser to stop")
		self.analyser.cpu_lock.acquire()
		log("Analyser is now stopped")
		log("Adding a new branch to the SGF tree")
		self.g.lock.acquire()
		new_branch=self.latest_node.parent.parent.parent.new_child(0)
		self.g.lock.release()
		
		move2undo=self.current_move-2
		
		log("Let's clean the analyser update_queue from requests for moves following move",move2undo)
		nb_request=self.analyser.update_queue.qsize()
		requests=[]
		for r in range(nb_request):
			priority,msg=self.analyser.update_queue.get()
			if type(msg)==type(123):
				if msg<=move2undo:
					log("keeping",(priority,msg))
					requests.append((priority,msg))
					#self.analyser.update_queue.put((priority,msg))
				else:
					log("discarding",(priority,msg))
			else:
				log("keeping",(priority,msg))
				requests.append((priority,msg))
		for r in requests:
			self.analyser.update_queue.put(r)
		
		log("Sending a priority request to undo move",move2undo,"and beyong to analyser")
		self.analyser.update_queue.put((1./move2undo,"undo "+str(move2undo)))
		log("Releasing the analyser")
		self.analyser.cpu_lock.release()

		self.latest_node=new_branch
		if type(self.black)!=type("abc"):
			#black is a bot
			self.black.undo()
			self.black.undo()
		if type(self.white)!=type("abc"):
			#white is a bot
			self.white.undo()
			self.white.undo()
		self.history.pop()
		self.grid,self.markup=self.history.pop()
		self.current_move-=2
		self.game_label.config(text=_("Currently at move %i")%self.current_move)
		self.parent.after(100,self.after_undo) #enough time for analyser to grab the process lock and process the queue

	def after_undo(self):
		self.pass_button.config(state='normal')
		if self.current_move>=3:
			self.undo_button.config(state='normal')	
		self.goban.display(self.grid,self.markup,freeze=False)


	def player_pass(self):
		log("The human is passing")
		color=self.next_color
		
		if color==1:
			if self.white_just_passed:
				log("End of the game")
				if type(self.white)!=type("abc"):
					#white is a bot
					result=self.white.final_score()
					show_info(self.white.bot_name+": "+result,parent=self.popup)
				return
		elif color==2:
			if self.black_just_passed:
				log("End of the game")
				if type(self.black)!=type("abc"):
					#black is a bot
					result=self.black.final_score()
					show_info(self.black.bot_name+": "+result,parent=self.popup)
				return

		
		self.next_color=3-color
		self.current_move+=1
		self.history.append([copy(self.grid),copy(self.markup)])
		self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
		self.goban.display(self.grid,self.markup)
		if color==1:
			self.g.lock.acquire()
			self.latest_node.set_move('b',None)
			self.g.lock.release()
			self.black_just_passed=True
			if type(self.white)!=type("abc"):
				#white is a bot
				log("Asking white (%s) to play the game move"%self.white.bot_name)
				self.white.place_black("pass")
			self.white_to_play()
		else:
			self.g.lock.acquire()
			self.latest_node.set_move('w',None)
			self.g.lock.release()
			self.white_just_passed=True
			if type(self.black)!=type("abc"):
				#black is a bot
				log("Asking black (%s) to play the game move"%self.black.bot_name)
				self.black.place_white("pass")
			self.black_to_play()
				
	def bot_to_play(self):
		
		self.gtp_thread.join(0.0)
		
		if self.gtp_thread.is_alive():
			#the bot is still thinking
			self.parent.after(250,self.bot_to_play)
			return
		self.cpu_lock.release()
		move=self.gtp_thread.answer
		
		color=self.next_color
		if move.lower()=="resign":
			log("The bot is resigning")
			if color==1:
				show_info(self.gtp_thread.bot.bot_name+" ("+_("Black")+"): "+move.lower(),parent=self.popup)
				self.goban.display(self.grid,self.markup)
				return
			elif color==2:
				show_info(self.gtp_thread.bot.bot_name+" ("+_("White")+"): "+move.lower(),parent=self.popup)
				self.goban.display(self.grid,self.markup)
				return
		elif move.lower()=="pass":
			log("The bot is passing")
			if color==1:
				show_info(self.gtp_thread.bot.bot_name+" ("+_("Black")+"): "+move.lower(),parent=self.popup)
				if self.white_just_passed:
					self.goban.display(self.grid,self.markup)
					result=self.gtp_thread.bot.final_score()
					show_info(self.gtp_thread.bot.bot_name+" ("+_("Black")+"): "+result,parent=self.popup)
					return
			elif color==2:
				show_info(self.gtp_thread.bot.bot_name+": "+move.lower(),parent=self.popup)
				if self.black_just_passed:
					self.goban.display(self.grid,self.markup)
					result=self.gtp_thread.bot.final_score()
					show_info(self.gtp_thread.bot.bot_name+": "+result,parent=self.popup)
					return
			self.next_color=3-color
			self.current_move+=1
			self.history.append([copy(self.grid),copy(self.markup)])
			self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
			self.goban.display(self.grid,self.markup,freeze=True)
			if color==1:
				self.g.lock.acquire()
				self.latest_node.set_move('b',None)
				self.g.lock.release()
				self.black_just_passed=True
				if type(self.white)!=type("abc"):
					#white is a bot
					log("Asking white (%s) to play the game move"%self.white.bot_name)
					self.white.place_black("pass")
				self.white_to_play()
			else:
				self.g.lock.acquire()
				self.latest_node.set_move('w',None)
				self.g.lock.release()
				self.white_just_passed=True
				if type(self.black)!=type("abc"):
					#black is a bot
					log("Asking black (%s) to play the game move"%self.black.bot_name)
					self.black.place_white("pass")
				self.black_to_play()
		else:
			i,j=gtp2ij(move)
			self.next_color=3-color
			self.current_move+=1
			self.game_label.config(text=_("Currently at move %i")%self.current_move)
			
			self.history.append([copy(self.grid),copy(self.markup)])
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
			self.markup[i][j]=0
			self.goban.display(self.grid,self.markup,freeze=True)
			
			if color==1:
				#black juste played
				self.g.lock.acquire()
				self.latest_node.set_move('b',(i,j))
				self.g.lock.release()
				self.black_just_passed=False
				if type(self.white)!=type("abc"):
					#white is a bot
					log("Asking white (%s) to play the game move"%self.white.bot_name)
					if not self.white.place_black(ij2gtp((i,j))):
						a=10/0
				self.white_to_play()
			else:
				#white just played
				self.g.lock.acquire()
				self.latest_node.set_move('w',(i,j))
				self.g.lock.release()
				self.white_just_passed=False
				if (type(self.black)!=type("abc")) and (self.white!="black"):
					#white and black are different bots
					log("Asking black (%s) to play the game move"%self.black.bot_name)
					if not self.black.place_white(ij2gtp((i,j))):
						a=10/0
				self.black_to_play()
		
	def black_to_play(self):
		result=self.pause_lock.acquire(False)
		if not result:
			self.parent.after(250,self.black_to_play)
			return
		self.pause_lock.release()
			
		log("======== move %i ========="%self.current_move)
		log("black to play")
		
		self.g.lock.acquire()
		self.latest_node = self.g.extend_main_sequence()
		self.g.lock.release()
		log("Sending request to analyse move",self.current_move,"to analyser")
		self.analyser.update_queue.put((self.current_move,self.current_move))
		self.pass_button.config(state='disabled')
		self.undo_button.config(state='disabled')
		if self.black=="human":
			self.goban.bind("<Button-1>",self.click)
			self.pass_button.config(state='normal')
			if self.current_move>=3:
				self.undo_button.config(state='normal',command=self.undo_as_black)
			self.goban.display(self.grid,self.markup,freeze=False)
		elif self.black=="analyser":
			self.goban.bind("<Button-1>",self.do_nothing)
			self.goban.display(self.grid,self.markup,freeze=True)
			self.analyser_to_play()
		else:
			#black is a bot
			self.goban.bind("<Button-1>",self.do_nothing)
			log("Starting black gtp thread")
			self.gtp_thread=threading.Thread(target=self.gtp_thread_wrapper,args=(self.black,"black"))
			self.gtp_thread.start()
			self.goban.display(self.grid,self.markup,freeze=True)
			self.bot_to_play()
	
	def white_to_play(self):
		result=self.pause_lock.acquire(False)
		if not result:
			self.parent.after(250,self.white_to_play)
			return
		self.pause_lock.release()
		
		log("======== move %i ========="%self.current_move)
		log("White to play")
		
		self.g.lock.acquire()
		self.latest_node = self.g.extend_main_sequence()
		self.g.lock.release()
		log("Sending request to analyse move",self.current_move,"to analyser")
		self.analyser.update_queue.put((self.current_move,self.current_move))
		self.pass_button.config(state='disabled')
		self.undo_button.config(state='disabled')
		if self.white=="human":
			self.goban.bind("<Button-1>",self.click)
			self.pass_button.config(state='normal')
			if self.current_move>=3:
				self.undo_button.config(state='normal',command=self.undo_as_white)
			self.goban.display(self.grid,self.markup,freeze=False)
		elif self.white=="analyser":
			self.goban.bind("<Button-1>",self.do_nothing)
			self.goban.display(self.grid,self.markup,freeze=True)
			self.analyser_to_play()
		elif self.white=="black":
			self.goban.bind("<Button-1>",self.do_nothing)
			log("Starting white gtp thread")
			self.gtp_thread=threading.Thread(target=self.gtp_thread_wrapper,args=(self.black,"white"))
			self.gtp_thread.start()
			self.bot_to_play()
		else:
			#white is a bot
			self.goban.bind("<Button-1>",self.do_nothing)
			log("Starting white gtp thread")
			self.gtp_thread=threading.Thread(target=self.gtp_thread_wrapper,args=(self.white,"white"))
			self.gtp_thread.start()
			self.goban.display(self.grid,self.markup,freeze=True)
			self.bot_to_play()
	
	def analyser_to_play(self):
		try:
			msg=self.analyser.best_moves_queue.get(False)
		except:
			self.parent.after(250,self.analyser_to_play)
			return
		log("received msg from analyser:",msg)
		number,move=msg
		if number<self.current_move:
			log("msg received by analyser is for previous move")
			log("analyser needs to wait for a new message")
			self.parent.after(1,self.analyser_to_play)
		elif number>self.current_move:
			log("msg received by analyser is for next move")
			log("probably a canceled move")
			log("analyser needs to wait for a new message")
			self.parent.after(1,self.analyser_to_play)
		elif number==self.current_move:
			log("this is the message analyser is waiting for")
			color=self.next_color
			if move.lower()=="resign":
				log("The analyser is resigning")
				if color==1:
					show_info(self.analyser.bot.bot_name+" ("+_("Black")+"): "+move.lower(),parent=self.popup)
					return
				elif color==2:
					show_info(self.analyser.bot.bot_name+" ("+_("White")+"): "+move.lower(),parent=self.popup)
					return
			elif move.lower()=="pass":
				log("The analyser is passing")
				if color==1:
					show_info(self.analyser.bot.bot_name+" ("+_("Black")+"): "+move.lower(),parent=self.popup)
					if self.white_just_passed:
						return
				elif color==2:
					show_info(self.analyser.bot.bot_name+" ("+_("White")+"): "+move.lower(),parent=self.popup)
					if self.black_just_passed:
						return
				self.next_color=3-color
				self.current_move+=1
				self.history.append([copy(self.grid),copy(self.markup)])
				self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
				self.goban.display(self.grid,self.markup,freeze=True)
				if color==1:
					self.g.lock.acquire()
					self.latest_node.set_move('b',None)
					self.g.lock.release()
					self.black_just_passed=True
					if type(self.white)!=type("abc"):
						#white is a bot
						log("Asking white (%s) to play the game move"%self.white.bot_name)
						self.white.place_black("pass")
					self.white_to_play()
				else:
					self.g.lock.acquire()
					self.latest_node.set_move('w',None)
					self.g.lock.release()
					self.white_just_passed=True
					if type(self.black)!=type("abc"):
						#black is a bot
						log("Asking black (%s) to play the game move"%self.black.bot_name)
						self.black.place_white("pass")
					self.black_to_play()
			else:
				i,j=gtp2ij(move)
				self.next_color=3-color
				self.current_move+=1
				self.game_label.config(text=_("Currently at move %i")%self.current_move)
				
				self.history.append([copy(self.grid),copy(self.markup)])
				place(self.grid,i,j,color)
				self.grid[i][j]=color
				self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
				self.markup[i][j]=0
				self.goban.display(self.grid,self.markup,freeze=True)
				
				if color==1:
					self.g.lock.acquire()
					self.latest_node.set_move('b',(i,j))
					self.g.lock.release()
					self.black_just_passed=False
					if type(self.white)!=type("abc"):
						#white is a bot
						log("Asking white (%s) to play the game move"%self.white.bot_name)
						self.white.place_black(ij2gtp((i,j)))
					self.white_to_play()
				else:
					self.g.lock.acquire()
					self.latest_node.set_move('w',(i,j))
					self.g.lock.release()
					self.white_just_passed=False
					if type(self.black)!=type("abc"):
						#black is a bot
						log("Asking black (%s) to play the game move"%self.black.bot_name)
						self.black.place_white(ij2gtp((i,j)))
					self.black_to_play()
			
			
	def do_nothing(self,event):
		pass
	
	def click(self,event):
		if self.locked:
			return
		dim=self.dim
		#add/remove black stone
		#check pointer location
		i,j=self.goban.xy2ij(event.x,event.y)
		color=self.next_color
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			print ("<click>")
			#inside the grid
			#what is under the pointer ?
			
			if self.grid[i][j] not in (1,2):
				#nothing, so we add a stone			
	
				self.history.append([copy(self.grid),copy(self.markup)])
					
				place(self.grid,i,j,color)
				self.grid[i][j]=color
				
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				self.next_color=3-color
				
				self.g.lock.acquire()
				node = self.latest_node
				if color==1:
					node.set_move("b", (i,j))
				else:
					node.set_move("w", (i,j))
				self.g.lock.release()
				
				
				self.current_move+=1
				self.game_label.config(text=_("Currently at move %i")%self.current_move)
				
				if self.next_color==1:
					self.white_just_passed=False
					if type(self.black)!=type("abc"):
						#black is a bot
						log("Asking black (%s) to play the game move"%self.black.bot_name)
						self.black.place_white(ij2gtp((i,j)))
					self.black_to_play()
				else:
					self.black_just_passed=False
					if type(self.white)!=type("abc"):
						#white is a bot
						log("Asking white (%s) to play the game move"%self.white.bot_name)
						self.white.place_black(ij2gtp((i,j)))
					self.white_to_play()
	
	def redraw(self, event):
		new_size=min(event.width,event.height)
		new_space=new_size/(self.dim+1+1)
		self.goban.space=new_space
		
		new_anchor_x=(event.width-new_size)/2.
		self.goban.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2.
		self.goban.anchor_y=new_anchor_y
		
		self.goban.redraw()

if __name__ == "__main__":
	top = Tk()
	popup = Toplevel(top)
	popup.parent=top
	LiveAnalysisLauncher(popup)
	top.mainloop()
