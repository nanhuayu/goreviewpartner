# -*- coding: utf-8 -*-

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves
from sys import exit,argv
from tkinter import *
import sys
import os

import configparser

from time import sleep
import os
import threading
import tkinter.ttk as ttk

from toolbox import *
from toolbox import _

import tkinter.messagebox


class LeelaZeroAnalysis():

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		
		leela_zero=self.leela_zero
		log()
		log("==============")
		log("move",str(current_move))
		
		#additional_comments=""
		if player_color in ('w',"W"):
			log("leela Zero play white")
			answer=leela_zero.play_white()
		else:
			log("leela Zero play black")
			answer=leela_zero.play_black()
		
		if current_move>1:
			es=leela_zero.get_leela_zero_final_score()
			#one_move.set("ES",es)
			save_position_data(one_move,self.data_in_comments,"ES",es,bot="Leela Zero")
			
		best_answer=answer
		save_position_data(one_move,self.data_in_comments,"CBM",answer,bot="Leela Zero") #Computer Best Move
		#additional_comments+="\n"+_("For this position, %s would %s"%("Leela Zero",answer.lower()))
		
		position_evaluation=leela_zero.get_all_leela_zero_moves()
		
		if (answer.lower() in ["pass","resign"]):
			if answer.lower()=="pass":
				log(" => Leela Zero would pass")
				leela_zero.undo()
			elif answer.lower()=="resign":
				log(" => Leela Zero would resign")
				if self.stop_at_first_resign:
					log("")
					log("The analysis will stop now")
					log("")
					self.move_range=[]
				else:
					leela_zero.undo_resign()
		else:
			#one_move.set("CBM",answer.lower()) #Computer Best Move
			
			#let's make sure there is at least one variation available
			if len(position_evaluation['variations'])==0:
				position_evaluation['variations'].append({'sequence':answer})
			
			nb_undos=1 #let's remember to undo that move from Leela Zero

			#let's make sure that there is more than one move for the first line of play
			#only one move could be a bookmove, or a very very forcing move
			first_sequence=position_evaluation['variations'][0]['sequence']
			new_sequence=first_sequence
			while len(new_sequence.split())<=1 and nb_undos<=5:
				log("first, let's ask leela zero for the next move")
				if player_color in ('w',"W") and nb_undos%2==0:
					answer=leela_zero.play_white()
				elif player_color in ('w',"W") and nb_undos%2==1:
					answer=leela_zero.play_black()
				elif player_color not in ('w',"W") and nb_undos%2==0:
					answer=leela_zero.play_black()
				else:
					answer=leela_zero.play_white()
				nb_undos+=1 #one have to remember to undo that move later
				
				new_position_evaluation=leela_zero.get_all_leela_zero_moves() #let's get stats for this new move
				
				#let's make sure there is at least one variation available
				if len(new_position_evaluation['variations'])==0:
					new_position_evaluation['variations'].append({'sequence':answer})
				
				if (answer.lower() not in ["pass","resign"]):
					#let's check the lenght of the new sequence
					new_sequence=new_position_evaluation["variations"][0]["sequence"]
					#adding this new sequence to the old sequence
					position_evaluation['variations'][0]['sequence']+=" "+new_sequence

				else:
					#leela zero does not want to play further on this line of play
					#so let's stop there
					break

			for u in range(nb_undos):
				#log("undo...")
				leela_zero.undo()
			
		best_move=True
		log("Number of alternative sequences:",len(position_evaluation['variations']))
		for variation in position_evaluation['variations'][:self.maxvariations]:
			#exemple: {'value network win rate': '50.22%', 'policy network value': '17.37%', 'sequence': 'Q16 D4 D17 Q4', 'playouts': '13', 'first move': 'Q16'}
			previous_move=one_move.parent
			current_color=player_color	
			first_variation_move=True
			for one_deep_move in variation['sequence'].split(' '):
				if one_deep_move.lower() in ["pass","resign"]:
					log("Leaving the variation when encountering",one_deep_move.lower())
					break

				i,j=gtp2ij(one_deep_move)
				new_child=previous_move.new_child()
				new_child.set_move(current_color,(i,j))
				
				if first_variation_move==True:
					first_variation_move=False
					#variation_comment=""
		
					if 'value network win rate' in variation:
						if player_color=='b':
							black_value=variation['value network win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['value network win rate']
							black_value=opposite_rate(white_value)	
						save_variation_data(new_child,self.data_in_comments,"VNWR",black_value+'/'+white_value)
						if best_move:
							save_position_data(one_move,self.data_in_comments,"VNWR",black_value+'/'+white_value,bot="Leela Zero")

					if 'policy network value' in variation:
						save_variation_data(new_child,self.data_in_comments,"PNV",variation['policy network value'])

					if 'playouts' in variation:
						save_variation_data(new_child,self.data_in_comments,"PLYO",variation['playouts'])
					
					#new_child.add_comment_text(variation_comment)
					
					if best_move:
						best_move=False
					
				previous_move=new_child
				if current_color in ('w','W'):
					current_color='b'
				else:
					current_color='w'
		log("==== no more sequences =====")
		
		#one_move.add_comment_text(additional_comments)
		return best_answer
	
	def initialize_bot(self):
		leela_zero=leela_zero_starting_procedure(self.g,self.profile)
		self.leela_zero=leela_zero
		self.time_per_move=0
		return leela_zero

def leela_zero_starting_procedure(sgf_g,profile="slow",silentfail=False):
	if profile=="slow":
		timepermove_entry="SlowTimePerMove"
	elif profile=="fast":
		timepermove_entry="FastTimePerMove"

	Config = configparser.ConfigParser()
	Config.read(config_file)

	leela_zero=bot_starting_procedure("LeelaZero","Leela Zero",Leela_Zero_gtp,sgf_g,profile,silentfail)
	if not leela_zero:
		return False
	try:
		time_per_move=Config.get("LeelaZero", timepermove_entry)
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move")
				leela_zero.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				#self.time_per_move=time_per_move #why is that needed???
	except:
		log("Wrong value for Leela thinking time:",Config.get("LeelaZero", timepermove_entry))
		log("Erasing that value in the config file")
		Config.set("LeelaZero",timepermove_entry,"")
		Config.write(open(config_file,"w"))
	
	return leela_zero



class RunAnalysis(LeelaZeroAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile)

class LiveAnalysis(LeelaZeroAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile="slow"):
		LiveAnalysisBase.__init__(self,g,filename,profile)


import ntpath
import subprocess
import threading,  queue

class Position(dict):
	def __init__(self):
		self['variations']=[]

class Variation(dict):
	pass

class Leela_Zero_gtp(gtp):

	def quick_evaluation(self,color):
		if color==2:
			answer=self.play_white()
		else:
			answer=self.play_black()
		
		all_moves=self.get_all_leela_zero_moves()
		
		if answer.lower()=="pass":
			self.undo()
		elif answer.lower()=="resign":
			self.undo_resign()
		else:
			self.undo()
		
		sequence_first_move,one_sequence,one_value_network,one_policy_network,one_nodes = all_moves[0]
		if color==1:
			black_win_rate=str(one_value_network)+'%'
			white_win_rate=str(100-one_value_network)+'%'
		else:
			black_win_rate=str(100-one_value_network)+'%'
			white_win_rate=str(one_value_network)+'%'
		return _("black/white win probability for this variation: ")+black_win_rate+'/'+white_win_rate

	def undo_resign(self):
		#apparently, Leela consider "resign" as a standard move that need to be undoed the same way as other move 
		#self.undo()
		pass #apparently, this has been "fixed" in v0.10, v0.11 or v0.12 :)
		
	def __init__(self,command):
		self.c=1
		leela_zero_working_directory=command[0][:-len(ntpath.basename(command[0]))]
		log("Leela Zero working directory:",leela_zero_working_directory)

		self.process=subprocess.Popen(command,cwd=leela_zero_working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		
		self.stderr_queue=queue.Queue()
		
		threading.Thread(target=self.consume_stderr).start()
	def get_leela_zero_final_score(self):
		self.write("final_score")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except:
			raise GtpException("GtpException in Get_leela_zero_final_score()")

	def get_leela_zero_influence(self):
		self.write("influence")
		one_line=self.readline() #empty line
		buff=[]
		while self.stderr_queue.empty():
			sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		buff.reverse()
		#log(buff)
		influence=[]
		for i in range(self.size):
			one_line=buff[i].strip()
			one_line=one_line.replace(".","0").replace("x","1").replace("o","2").replace("O","0").replace("X","0").replace("w","1").replace("b","2")
			one_line=[int(s) for s in one_line.split(" ")]
			influence.append(one_line)
		
		return influence

	def get_all_leela_zero_moves(self):
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()
		
		answers=[]
		
		position_evaluation=Position()
		
		for err_line in buff:
			#log(err_line)
			if " ->" in err_line:
				if err_line[0]==" ":
					#log(err_line)
					variation=Variation()
					
					one_answer=err_line.strip().split(" ")[0]
					variation["first move"]=one_answer
					
					nodes=err_line.strip().split("(")[0].split("->")[1].replace(" ","")
					variation["playouts"]=nodes
					
					value_network=err_line.split("(V:")[1].split('%')[0].strip()+"%"
					variation["value network win rate"]=value_network #for Leela Zero, the value network is used as win rate
					
					policy_network=err_line.split("(N:")[1].split('%)')[0].strip()+"%"
					variation["policy network value"]=policy_network
					
					sequence=err_line.split("PV: ")[1].strip()
					variation["sequence"]=sequence
					
					#answers=[[one_answer,sequence,value_network,policy_network,nodes]]+answers
					position_evaluation['variations']=[variation]+position_evaluation['variations']

		return position_evaluation

from leela_analysis import LeelaSettings

class LeelaZeroSettings(LeelaSettings):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.name="LeelaZero"
		self.initialize()


class LeelaZeroOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='Leela Zero'
		self.my_starting_procedure=leela_zero_starting_procedure

LeelaZero={}
LeelaZero['name']="LeelaZero"
LeelaZero['gtp_name']="Leela Zero"
LeelaZero['analysis']=LeelaZeroAnalysis
LeelaZero['openmove']=LeelaZeroOpenMove
LeelaZero['settings']=LeelaZeroSettings
LeelaZero['gtp']=Leela_Zero_gtp
LeelaZero['liveanalysis']=LiveAnalysis
LeelaZero['runanalysis']=RunAnalysis
LeelaZero['starting']=leela_zero_starting_procedure

import getopt
if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = open_sgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			sys.exit()
		log("filename:",filename)
		top = Tk()
		bot=LeelaZero
		
		slowbot=bot
		slowbot['profile']="slow"
		fastbot=dict(bot)
		fastbot['profile']="fast"
		RangeSelector(top,filename,bots=[slowbot, fastbot]).pack()
		top.mainloop()
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['no-gui','range=', 'color=', 'komi=',"variation="])
		except Exception as e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		top=None
		batch=[]
		
		for filename in parameters[1]:
			
			move_selection,intervals,variation,komi,nogui=parse_command_line(filename,parameters[0])
			if nogui:
				log("File to analyse:",filename)
				app=RunAnalysis("no-gui",filename,move_selection,intervals,variation-1,komi)
				app.terminate_bot()
			else:
				if not top:
					top = Tk()
					top.withdraw()
				one_analysis=[RunAnalysis,filename,move_selection,intervals,variation-1,komi]
				batch.append(one_analysis)
		
		if not nogui:
			top.after(1,lambda: batch_analysis(top,batch))
			top.mainloop()
