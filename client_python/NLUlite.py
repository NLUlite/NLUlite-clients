#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NLUlite is a high-level Natural Language Understanding
framework. 

This file is the client part of the framework. This file is released
with BSD license.
"""

__author__  = 'NLUlite'
__version__ = '0.1.2'
__license__ = 'BSD'


import socket, copy
import xml.etree.ElementTree as ET
import string, urllib2
from HTMLParser import HTMLParser
from xml.sax.saxutils import unescape
import os

class NLUliteHTMLParser(HTMLParser):
    """
    Helper class for Wisdom.add_url()
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.current_tag = ''
        self.all_text = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag= tag

    def handle_data(self, data):
        tag= self.current_tag
        if tag != 'script' and tag != 'img':
            self.all_text += data

    def get_all_text(self):
        return self.all_text

class NLUliteWikiParser(HTMLParser):
    """
    Helper class for Wisdom.add_url()
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.current_tag = ''
        self.all_text = ''
        self.p_tag = False

    def handle_starttag(self, tag, attrs):
        self.current_tag= tag
        if tag == 'p':
            self.p_tag = True

    def handle_endtag(self, tag):
        self.current_tag= tag
        if tag == 'p':
            self.p_tag = False
            self.all_text += '\n'            

    def handle_data(self, data):
        tag= self.current_tag
        if self.p_tag:
            self.all_text += data

    def get_all_text(self):
        return self.all_text


class HTMLTemplateFactory():
    
    def __init__(self):
        return

    def get(self,url):
        if(url.find('wikipedia') != -1):
            return NLUliteWikiParser()
        return NLUliteHTMLParser()
    


class NLUliteFeedParser(HTMLParser):
    """
    Helper class for Wisdom.add_url()
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.current_tag = ''
        self.all_text = ''

    def handle_starttag(self, tag, attrs):
        self.current_tag= tag

    def handle_data(self, data):
        tag= self.current_tag
        if tag == 'title':
            self.all_text += '[% feed %]'
            self.all_text += data + ' \r\n\r\n'
        if tag == 'description':
            self.all_text += data + ' \r\n\r\n'

    def get_all_text(self):
        return self.all_text


class FeedTemplateFactory():
    
    def __init__(self):
        return

    def get(self,url):
        return NLUliteFeedParser()


class Rule:
    """
    Store one single rule item
    """
    def __init__(self):
        self.text= ''
        self.description= ''
        self.weight= 1

class QPair:
    """
    Store the query/reply combination in an answer
    """
    def __init__(self, query='', reply= ''):
        self.query= query
        self.reply= reply


class AnswerElement:
    """
    Store one single answer item
    """
    def __init__(self):
        self.text= ''
        self.description= ''
        self.drs= ''
        self.weight= 1
        self.pairs= []
        self.rules= []
        self.wisdom = ''

    def comment(self):
        writer = Writer(self.wisdom)
        return_string  = "\n"
        for pair in self.pairs:
            if pair.reply != None and pair.query != None:
                return_string += pair.query + ': ' + pair.reply + '\n'
        for rule in self.rules:                        
            if rule.text == None:
                continue
            return_string += rule.text
            if rule != self.rules[-1]:
                return_string += '+' 
        if self.text != None:
            return_string += self.text + "\n"
        return_string += "\n"
        return return_string
        

class Answer:
    """
    Store all the answer information
    """
    def __init__(self,wisdom):        
        self.answer_elements= []
        self.question_ID= ''
        self.wisdom= wisdom
        self.status= ''

    def __sort__(self):
        self.answer_elements = sorted( self.answer_elements, key= lambda item : item.weight )

    def set_elements(self,answer_elements):
        self.answer_elements= answer_elements

    def set_question_ID(self,qID):
        self.question_ID= qID

    def elements(self,query=""):
        if query == "":
            return self.answer_elements
        else:
            return_list= []
            for item in self.answer_elements:
                new_item = copy.deepcopy(item)
                new_item.pairs = []
                for pair in item.pairs:
                    if pair.query.find(query) != -1:
                        new_item.pairs.append(pair)
                return_list.append(new_item)
            return return_list

    def is_positive(self):
        if self.status.find('yes') != -1 or self.status.find('list') != -1:
            return True
        return False

    def is_negative(self):
        if self.status.find('no') != -1:
            return True
        return False

    def is_list(self):
        if self.status.find('list') != -1:
            return True
        return False

    def match(self,text):
        for item in self.answer_elements:
            drs= item.drs
            answer= self.wisdom.__match_drs_with_text__(drs,text)
            if answer.is_positive():
                return answer
        ret_answ= self
        ret_answ.answer_elements= []
        ret_answ.question_ID= ''
        ret_answ.status= ''
        return ret_answ

    def comment(self):
        writer = Writer(self.wisdom)
        return writer.write(self)

    def join(self,rhs):
        if self.is_positive() and rhs.is_list():
            self.status      = rhs.status
            self.question_ID = rhs.question_ID
            self.wisdom      = rhs.wisdom
        if self.is_negative() and rhs.is_positive():
            self.status      = rhs.status
            self.question_ID = rhs.question_ID
            self.wisdom      = rhs.wisdom
        self.answer_elements.extend(rhs.answer_elements)
        self.__sort__()
        
        
def join_answers(answer_list) :
    """
    Joins together and sorts a list of answers
    """
    answers = answer_list[0]
    for item in answer_list[1:] :
        answers.join(item)
    return answers

        
class WisdomParameters:
    def __init__(self):
        self.num_answers    = 10
        self.accuracy_level = 5
        self.solver_options = ''
        self.skip_presuppositions = ''
        self.skip_solver = 'false'
        self.add_data = 'true'
        self.timeout = 10

    def set_num_answers(self, num):
        self.num_answers    = num
    def set_accuracy_level(self, num):
        self.accuracy_level = num
    def set_solver_options(self, options):
        self.solver_options = options
    def set_skip_presuppositions(self, options):
        self.skip_presuppositions = options
    def set_skip_solver(self, options):
        self.skip_solver = options
    def set_add_data(self, options):
        self.add_data = options
    def set_timeout(self, options):
        self.timeout = options


    def get_num_answers(self):
        return self.num_answers
    def get_accuracy_level(self):
        return self.accuracy_level
    def get_solver_options(self):
        return self.solver_options
    def get_skip_presuppositions(self):
        return self.skip_presuppositions
    def get_skip_solver(self):
        return self.skip_solver
    def get_add_data(self):
        return self.add_data
    def get_timeout(self):
        return self.timeout

        
class Wisdom:
    """
    Process the wisdom
    """
    def __init__(self, server):
        if not isinstance(server, ServerProxy):
            raise TypeError('The server attribute must be set to an instance of NLUlite.ServerProxy')
        self.server= server
        self.ID= self.server.get_new_ID()

    def __match_drs_with_text__(self,drs,question):
        reply = self.server.match_drs(drs,question,self.ID)
        answer= self.__process_query_reply__(reply)
        return answer

    def __process_query_reply__(self,reply):
        answer_elements= []
        if reply == "":
            return Answer(self)
        root= ET.fromstring(reply)
        qID= status= ''
        for child in root: 
            if child.tag == 'qID':
                qID= child.text
                continue
            if child.tag == 'status':
                status= child.text
                continue

            text=''
            link=''
            drs=''
            weight=1
            pairs= []
            rules= []
            
            for c2 in child:
                if c2.tag == 'text':
                    text= c2.text
                if c2.tag == 'link':
                    link= c2.text
                if c2.tag == 'drs':
                    drs= c2.text
                if c2.tag == 'weight':
                    weight= c2.text
                if c2.tag == 'data':
                    for c3 in c2:    # <dataitem>
                        WP= name= ''
                        for c4 in c3:
                            if c4.tag == 'WP':
                                WP= c4.text
                            if c4.tag == 'name':
                                name= c4.text
                        pairs.append( QPair(WP,name) )
                if c2.tag == 'rules':
                    for c3 in c2:   # <ruleitem>
                        rule = Rule()                        
                        for c4 in c3:
                            if c4.tag == 'text':
                                rule.text = c4.text
                            if c4.tag == 'link':
                                rule.description= c4.text
                        rules.append( rule )

            answ= AnswerElement()
            answ.text   = text
            answ.description = link
            answ.drs    = drs
            answ.weight = weight
            answ.pairs  = pairs
            answ.rules  = rules
            answ.wisdom = self
            answer_elements.append( answ )
            
        answer= Answer(self)
        answer.set_elements(answer_elements)
        answer.set_question_ID(self.ID + ':' + qID.rstrip().lstrip() + ':' + str(answer_elements.__len__()) )
        answer.status= status

        return answer

    def add(self, text):    
        reply = self.server.add_data(text, self.ID);

    def add_file(self, filename):
        filename = os.path.expanduser(filename)
        text = open(filename, 'r').read()
        reply = self.server.add_data(text, self.ID);

    def add_url(self, url):
        req = urllib2.Request(url, headers={'User-Agent' : "urrlib2 - NLUlite dummy browser"}) 
        page= urllib2.urlopen(req).read()
        parser = HTMLTemplateFactory().get(url)
        parser.feed(page)
        webtext = parser.get_all_text()
        webtext.decode('utf-8')
        self.add(webtext)

    def add_feed(self, url):
        req = urllib2.Request(url, headers={'User-Agent' : "urrlib2 - NLUlite dummy feeder"}) 
        page= urllib2.urlopen(req).read()
        page = unescape( page )
        feeder = FeedTemplateFactory().get(url)
        feeder.feed(page)        
        text = feeder.get_all_text()
        text.decode('utf-8')        
        self.add(text)

    def save(self, filename):
        filename = os.path.expanduser(filename)
        reply = self.server.save_wisdom(self.ID);
        f= open(filename, "w")
        f.write(reply);
        f.close();

    def save_rdf(self, filename):
        filename = os.path.expanduser(filename)
        reply = self.server.save_rdf(self.ID);
        f= open(filename, "w")
        f.write(reply);
        f.close();


    def save_string(self):
        reply = self.server.save_wisdom(self.ID);
        return reply

    def load(self, filename):        
        filename = os.path.expanduser(filename)
        f= open(filename, "r")
        data= f.read()
        f.close();
        reply = self.server.load_wisdom(data, self.ID);

    def load_string(self, string):
        data= string
        reply = self.server.load_wisdom(data, self.ID);

    def ask(self, question):
        reply = self.server.query(question, self.ID)
        answer= self.__process_query_reply__(reply)
        return answer

    def match(self, question):
        reply = self.server.match(question, self.ID)
        answer= self.__process_query_reply__(reply)
        return answer

    def export_to_server(self,key,password="",timer=-1):
        reply = self.server.send_to_publish(self.ID, key, password,timer);
        if(reply == "<error>"):
            raise RuntimeError('Cannot publish wisdom: The key ' + key + ' is already in use.')

    def import_from_server(self,key):
        reply = self.server.get_from_published(self.ID, key);
        if(reply == "<error>"):
            raise RuntimeError('Cannot retrieve wisdom: The key ' + key + ' does not exist')
        self.ID= reply;  # This function erases the wisdom when succesful

    def clear(self):
        reply = self.server.clear_wisdom(self.ID);
        if(reply == "<error>"):
            raise RuntimeError('Cannot clear wisdom: The Wisdom.ID ' + self.ID + ' does not exist')

    def set_wisdom_parameters(self, wp):
        if not isinstance(wp, WisdomParameters):
            raise TypeError('The wisdom.set_wisdom_parameters attribute must be set to an instance of NLUlite.WisdomParameters')        
        self.server.set_wisdom_parameters(self.ID, wp);

class Writer:
    """
    Writer class
    """
    def __init__(self, wisdom):
        if not isinstance(wisdom, Wisdom):
            raise TypeError('The wisdom attribute must be set to an instance of NLUlite.Wisdom')
        self.server = wisdom.server
        reply= self.server.get_new_writer_ID(wisdom.ID)
        self.ID= reply

    def __del__(self):
        self.server.writer_erase(self.ID);

    def write(self, answer):
        if isinstance(answer, AnswerElement):
            reply= self.server.writer_write(self.ID, answer.drs)
            return reply
        if isinstance(answer, Answer):
            reply= self.server.writer_write_answer(self.ID, answer.question_ID)
            return reply
        raise TypeError('The answer attribute must be set to an instance of NLUlite.Anwer or NLUlite.AnswerElement')

            
class ServerProxy:
    """
    Server class
    """
    def __init__(self, ip= "localhost", port= 4001):
        self.ip   = ip
        self.port = port
        self.wisdom_list= []
        self.published_list= []
        reply= self.__send('<test>\n<eof>')
        if reply != '<ok>':
            raise RuntimeError('No valid server seems to be running.')

    def __del__(self):
        for item in self.wisdom_list:
            if(item not in self.published_list):
                self.erase(item)

    def add_data(self, data, ID):
        text = '<data ID=' + ID + '>'
        text += data
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def save_wisdom(self, ID):
        text = '<save ID=' + ID + '>'
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def save_rdf(self, ID):
        text = '<save_rdf ID=' + ID + '>'
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def load_wisdom(self, data, ID):
        text = '<load ID=' + ID + '>'
        text += data
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def query(self, data, ID):
        text = '<question ID=' + ID + '>'
        text += data
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def match(self, data, ID):
        text = '<match ID=' + ID + '>'
        text += data
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def match_drs(self, drs, question, ID):
        text = '<match_drs ID=' + ID + '>'
        text += drs
        text += ";"
        text += question
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def erase(self, ID):
        text = '<erase ID=' + ID + '>'
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def get_new_ID(self):
        text = '<new_wisdom>\n'
        text += '<eof>'
        ID = self.__send(text)
        self.wisdom_list.append(ID)
        return ID

    def get_new_writer_ID(self, wisdom_ID):
        text = '<writer_new ID=' + wisdom_ID + '>'
        text += '<eof>'
        ID = self.__send(text)
        return ID

    def writer_erase(self, writer_ID):
        text = '<writer_erase ID=' + writer_ID + '>'
        text += '<eof>'
        ID = self.__send(text)
        return ID

    def writer_write(self, writer_ID, drs):
        text = '<writer_write ID=' + writer_ID + '>'
        text += drs
        text += '<eof>'
        ID = self.__send(text)
        return ID

    def writer_write_answer(self, writer_ID, qID):
        text = '<writer_write_answer ID=' + writer_ID + '>'
        text += qID.rstrip().lstrip()
        text += '<eof>'
        ID = self.__send(text)
        return ID

    def send_to_publish(self, ID, publish_key, password, timer):
        text = '<publish ID=' + ID + ' key=' + publish_key + ' passwd=' + password + ' timer=' + str(timer) + '>'
        text += '<eof>'
        reply = self.__send(text)
        if(reply != "<error>"):
            self.published_list.append(ID);
        return reply

    def get_from_published(self, ID, publish_key):
        text = '<get_published ID=' + ID + ' key=' + publish_key + '>'
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def clear_wisdom(self, ID):
        text = '<erase_wisdom ID=' + ID + '>'
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def set_wisdom_parameters(self, ID, wp):
        accuracy_level = wp.get_accuracy_level()
        num_answers    = wp.get_num_answers()
        solver_options = wp.get_solver_options()
        skip_presuppositions = wp.get_skip_presuppositions()
        skip_solver = wp.get_skip_solver()
        add_data = wp.get_add_data()
        timeout = wp.get_timeout()
        text = ('<wisdom_parameters ' 
                + ' accuracy_level=' + str(accuracy_level) 
                + ' num_answers=' + str(num_answers) 
                + ' solver_options=' + solver_options 
                + ' skip_presuppositions=' + skip_presuppositions 
                + ' skip_solver=' + skip_solver 
                + ' add_data=' + add_data 
                + ' ID=' + ID
                + ' timeout=' + str(timeout)
                + '>'
        )
        text += '<eof>'
        reply = self.__send(text)
        return reply

    def erase_exported(self, publish_key, password= ""):
        text = '<erase_published' + ' key=' + publish_key + ' passwd=' + password + '>'
        text += '<eof>'
        reply = self.__send(text)
        if reply == "<error>":
            raise RuntimeError('Erasing published Wisdom: wrong key or password.')
        return

    def list_exported(self):
        text = '<list_published>'
        text += '<eof>'
        reply = self.__send(text)
        plist= []
        root= ET.fromstring(reply)
        for item in root:
            plist.append(item.text)
        return plist

    def get_new_ID(self):
        text = '<new_wisdom>\n'
        text += '<eof>'
        ID = self.__send(text)
        self.wisdom_list.append(ID)
        return ID

    def set_num_threads(self, num_threads):
        text = '<server threads=' + str(num_threads) +'>\n'
        text += '<eof>'
        ID = self.__send(text)
        self.wisdom_list.append(ID)
        return ID


    def __send(self, text): 
        """
        Helper function for sending information on a socket.  Send the 'text'
        and return the 'answer'.
        """
        sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect( (self.ip,self.port) )
# Send the question to the server
        totalsent= 0
        while totalsent < len(text):
            sent= sock.send(text[totalsent:])
            totalsent += sent
# Receive the answer
        answer= answerold= ''
        CHUNKLEN= 256
        while len(answerold) <= len(answer):
            answerold = answer
            chunk= sock.recv(CHUNKLEN)
            if chunk == '':
                break
            answer += chunk
        return answer

class Match:
    """
    Binds a text to a python function
    """
    def __init__(self,text):
        self.text= text
        self.function_list= []

    def __execute__(self,argument):
        answer= argument.match(self.text) # The argument can be a Wisdom or an Answer (they both have the method match() )
        if answer.is_positive(): 
            for function in self.function_list:
                function(answer)    

    def bind(self,function):
        self.function_list.append(function)



class Commands:
    """
    Manages the command list
    """
    def __init__(self,argument):
        if not isinstance(argument,Wisdom) and not isinstance(argument,Answer):
            raise TypeError('The argument in Commands() must be set to an instance of NLUlite.Wisdom or NLUlite.Answer')
        self.wisdom= argument
        self.match_list= []
    
    def parse(self,argument):
        self.wisdom= argument
    
    def add(self,match):
        if not isinstance(match,Match):
            raise TypeError('The match attribute in Commands.add() must be set to an instance of NLUlite.Match')
        self.match_list.append(match)

    def execute(self):
        for match in self.match_list:       
            match.__execute__(self.wisdom)
            
            
