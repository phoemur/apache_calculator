#!/usr/bin/env python3

import datetime
import os
import tkinter
import sqlite3
import xml.etree.ElementTree
import xml.parsers.expat
import xml.sax.saxutils

from collections import OrderedDict
from math import floor
from tkinter import ttk, messagebox
from tkinter.filedialog import asksaveasfilename, askopenfilename


class MainWindow(tkinter.Tk):
    def __init__(self):
        # Data Structures
        self.temp_score = OrderedDict([('< 29.9', 4), ('30.0 - 31.9', 3), ('32.0 - 33.9', 2), ('34.0 - 35.9', 1),
                                       ('36.0 - 38.4', 0), ('38.5 - 38.9', 1), ('39.0 - 40.9', 3), ('> 41.0', 4)])
        self.pa_score = OrderedDict([('< 49', 4), ('50 - 69', 2), ('70 - 109', 0), ('110 - 129', 2),
                                     ('130 - 159', 3), ('> 160', 4)])
        self.fc_score = OrderedDict([('< 39', 4), ('40 - 54', 3), ('55 - 69', 2), ('70 - 109', 0),
                                     ('110 - 139', 2), ('140 - 179', 3), ('> 180', 4)])
        self.fr_score = OrderedDict([('< 5', 4), ('6 - 9', 2), ('10 - 11', 1), ('12 - 24', 0),
                                     ('25 - 34', 1), ('35 - 49', 3), ('> 50', 4)])
        self.pao2_score = OrderedDict([('PaO2 < 55', 4), ('PaO2 55 - 60', 3), ('PaO2 61 - 70', 1),
                                       ('<200 ou PaO2 > 70', 0), ('200 - 349', 2), ('350 - 499', 3), ('> 500', 4)])
        self.ph_score = OrderedDict([('<7.15; <15', 4), ('7.15-7.24; 15-17.9', 3), ('7.25-7.32; 18-22.9', 2),
                                     ('7.33-7.49; 23-31.9', 0), ('7.50-7.59; 32-40.9', 1),
                                     ('7.60-7.69; 41-51.9', 3), ('>7.70; >52', 4)])
        self.na_score = OrderedDict([('< 110', 4), ('111 - 119', 3), ('120 - 129', 2), ('130 - 149', 0),
                                     ('150 - 154', 1), ('155 - 159', 2), ('160 - 179', 3), ('> 180', 4)])
        self.k_score = OrderedDict([('< 2.5', 4), ('2.5 - 2.9', 2), ('3 - 3.4', 1), ('3.5 - 5.4', 0),
                                    ('5.5 - 5.9', 1), ('6 - 6.9', 3), ('> 7', 4)])
        self.cr_score = OrderedDict([('< 0.6', 2), ('0.6-1.4', 0), ('1.5-1.9', 2), ('1.5-1.9 com IRA', 4),
                                     ('2-3.4', 3), ('2-3.4 com IRA', 6), ('> 3.5', 4), ('> 3.5 com IRA', 8)])
        self.ht_score = OrderedDict([('< 20', 4), ('20 - 29.9', 2), ('30 - 45.9', 0), ('46 - 49.9', 1),
                                     ('50 - 59.9', 2), ('> 60', 4)])
        self.leuc_score = OrderedDict([('< 1', 4), ('1 - 2.9', 2), ('3 - 14.9', 0), ('15 - 19.9', 1),
                                       ('20 - 39.9', 2), ('> 40', 4)])

        # Db
        self.filename = os.path.join(os.path.dirname(__file__), "patients.sdb")
        self.db = self.connect(self.filename)

        # GUI
        tkinter.Tk.__init__(self)
        self.wm_title("Calculadora do Score Apache-II")
        self.protocol("WM_DELETE_WINDOW", self.sair)
        self.resizable(tkinter.FALSE, tkinter.FALSE)

        self.images_keepmem = []
        self.icon = tkinter.PhotoImage(file=os.path.join(os.path.dirname(__file__), "images", "bookmark.gif"))
        self.images_keepmem.append(self.icon)
        self.tk.call('wm', 'iconphoto', self._w, self.icon)

        # Menus
        menubar = tkinter.Menu(self)
        self["menu"] = menubar
        self.option_add('*tearOff', tkinter.FALSE)

        # Menu Arquivo
        menuArquivo = tkinter.Menu(menubar)
        for label, command, shortcut_text, shortcut in (
                ("Novo", self.novo, "Ctrl+N", "<Control-n>"),
                ("Salvar", self.salvar, "Ctrl+S", "<Control-s>"),
                ("Excluir", self.remover, "Ctrl+E", "<Control-e>"),
                (None, None, None, None),
                ("Fechar", self.sair, "Ctrl+Q", "<Control-q>")):
            if label is None:
                menuArquivo.add_separator()
            else:
                menuArquivo.add_command(label=label, underline=0,
                                        command=command, accelerator=shortcut_text)
                self.bind(shortcut, command)
        menubar.add_cascade(label="Arquivo", menu=menuArquivo, underline=0)

        # Menu Editar
        menuEditar = tkinter.Menu(menubar)
        for label, command, shortcut_text, shortcut in (
                ("Copiar", self.copiar, "Ctrl+C", "<Control-c>"),
                ("Colar", self.colar, "Ctrl+V", "<Control-v>"),
                ("Recortar", self.recortar, "Ctrl+X", "<Control-x>")):
            menuEditar.add_command(label=label, underline=0 if label != "Colar" else 1,
                                   command=command, accelerator=shortcut_text)
            # self.bind(shortcut, command)
        menuEditar.add_separator()
        menuEditar.add_command(label="Importar XML", underline=0, command=self.importar_db)
        menuEditar.add_command(label="Exportar XML", underline=0, command=self.exportar_db)

        menubar.add_cascade(label="Editar", menu=menuEditar, underline=0)

        # Menu Ajuda
        menuAjuda = tkinter.Menu(menubar)
        menuAjuda.add_command(label="Mortalidade", underline=0,
                              command=self.mortalidade, accelerator="Ctrl+M")
        menuAjuda.add_command(label="Sobre", underline=0,
                              command=self.sobre, accelerator="Ctrl+H")
        self.bind("<Control-h>", self.sobre)
        self.bind("<Control-m>", self.mortalidade)
        menubar.add_cascade(label="Ajuda", menu=menuAjuda, underline=2)

        # Menu Mouse
        self.MENUmouse = tkinter.Menu(self, tearoff=0)
        self.MENUmouse.add_command(label="Copiar")
        self.MENUmouse.add_command(label="Colar")
        self.MENUmouse.add_command(label="Recortar")
        self.bind("<Button-3><ButtonRelease-3>", self.show_mouse_menu)

        # Toolbar
        self.mainframe = tkinter.Frame(self)
        self.toolbar = tkinter.Frame(self.mainframe)
        for image, command in (
                ("images/filenew.gif", self.novo),
                ("images/trash.gif", self.remover),
                ("images/filesave.gif", self.salvar),
                ("images/exit.gif", self.sair)):
            image = os.path.join(os.path.dirname(__file__), image)
            try:
                image = tkinter.PhotoImage(file=image)
                self.images_keepmem.append(image)
                button = tkinter.Button(self.toolbar, image=image,
                                        command=command)
                button.grid(row=0, column=len(self.images_keepmem) - 2)
            except tkinter.TclError as err:
                print(err)

        self.toolbar.grid(row=0, column=0, columnspan=5, sticky=tkinter.NW)
        self.mainframe.grid(row=0, column=0, sticky=tkinter.EW)

        # Nome
        ttk.Label(self.mainframe, text="Nome: ").grid(row=1, column=1, sticky=tkinter.W)
        self.nome = tkinter.StringVar()
        self.name_entry = ttk.Combobox(self.mainframe, width=50, textvariable=self.nome)
        self.name_entry.grid(row=1, column=2, columnspan=9, sticky=tkinter.W)
        self.name_entry['values'] = self.list_pac(self.db)
        self.name_entry.bind('<<ComboboxSelected>>', self.abrir_nome)

        # Sexo
        ttk.Label(self.mainframe, text='Sexo: ').grid(row=2, column=1, sticky=tkinter.W)
        self.sexo = tkinter.StringVar()
        self.sexframe = tkinter.Frame(self.mainframe)
        self.sexframe.grid(row=2, column=2, columnspan=10, sticky=tkinter.EW)

        self.masculino = ttk.Radiobutton(self.sexframe, text='Masculino', variable=self.sexo, value='Masculino', command=self.callback)
        self.feminino = ttk.Radiobutton(self.sexframe, text='Feminino', variable=self.sexo, value='Feminino', command=self.callback)
        self.masculino.grid(row=1, column=1, sticky=tkinter.W)
        self.feminino.grid(row=1, column=2, sticky=tkinter.W)

        # Data de nascimento
        self.ageframe = tkinter.Frame(self.mainframe)
        self.ageframe.grid(row=3, column=1, columnspan=10, sticky=tkinter.EW)
        ttk.Label(self.ageframe, text='Data de\nNascimento: ').grid(row=1, column=1, sticky=tkinter.W)
        self.dia_nasc = tkinter.StringVar()
        self.dia_nasc.set('01')
        self.mes_nasc = tkinter.StringVar()
        self.mes_nasc.set('Janeiro')
        self.ano_nasc = tkinter.StringVar()
        self.ano_nasc.set('1980')
        self.idade = tkinter.StringVar()
        ttk.Entry(self.ageframe, width=4, textvariable=self.dia_nasc).grid(row=1, column=2, sticky=tkinter.E)
        ttk.Label(self.ageframe, text='/').grid(row=1, column=3, sticky=tkinter.EW)
        self.mes = ttk.Combobox(self.ageframe, textvariable=self.mes_nasc)
        self.mes.grid(row=1, column=4, sticky=tkinter.EW)
        ttk.Label(self.ageframe, text='/').grid(row=1, column=5, sticky=tkinter.EW)
        ttk.Entry(self.ageframe, width=6, textvariable=self.ano_nasc).grid(row=1, column=6, sticky=tkinter.W)
        self.mes['values'] = ('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                              'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro')

        ttk.Label(self.ageframe, text='Idade: ').grid(row=1, column=7, sticky=tkinter.E)
        ttk.Label(self.ageframe, textvariable=self.idade).grid(row=1, column=8, sticky=tkinter.W)
        ttk.Label(self.ageframe, text='anos').grid(row=1, column=9, sticky=tkinter.E)
        self.mes.bind('<<ComboboxSelected>>', self.callback)
        self.dia_nasc.trace("w", self.callback)
        self.ano_nasc.trace("w", self.callback)

        # Temperatura
        ttk.Label(self.mainframe, text='Temperatura (°C): ').grid(row=4, column=1, sticky=tkinter.W)
        self.temperatura = tkinter.StringVar()
        self.temp = ttk.Combobox(self.mainframe, textvariable=self.temperatura)
        self.temp.grid(row=4, column=2, sticky=tkinter.W)
        self.temp['values'] = tuple(self.temp_score.keys())
        self.temperatura.set(self.temp['values'][4])
        self.temp.bind('<<ComboboxSelected>>', self.callback)

        # Pressão Arterial Média
        ttk.Label(self.mainframe, text='Pressão Arterial\nMédia (mmHg): ').grid(row=5, column=1, sticky=tkinter.W)
        self.pam = tkinter.StringVar()
        self.PA = ttk.Combobox(self.mainframe, textvariable=self.pam)
        self.PA.grid(row=5, column=2, sticky=tkinter.W)
        self.PA['values'] = tuple(self.pa_score.keys())
        self.pam.set(self.PA['values'][2])
        self.PA.bind('<<ComboboxSelected>>', self.callback)

        # Frequência Cardíaca
        ttk.Label(self.mainframe, text='Frequência\nCardíaca: ').grid(row=6, column=1, sticky=tkinter.W)
        self.fc = tkinter.StringVar()
        self.FREQ = ttk.Combobox(self.mainframe, textvariable=self.fc)
        self.FREQ.grid(row=6, column=2, sticky=tkinter.W)
        self.FREQ['values'] = tuple(self.fc_score.keys())
        self.fc.set(self.FREQ['values'][3])
        self.FREQ.bind('<<ComboboxSelected>>', self.callback)

        # Frequência Respiratória
        ttk.Label(self.mainframe, text='Frequência\nRespiratória: ').grid(row=7, column=1, sticky=tkinter.W)
        self.fr = tkinter.StringVar()
        self.FR = ttk.Combobox(self.mainframe, textvariable=self.fr)
        self.FR.grid(row=7, column=2, sticky=tkinter.W)
        self.FR['values'] = tuple(self.fr_score.keys())
        self.fr.set(self.FR['values'][3])
        self.FR.bind('<<ComboboxSelected>>', self.callback)

        # PA02
        ttk.Label(self.mainframe, text='A-aPO2(FiO2>50%)\nou PaO2(FiO2<50%):').grid(row=8, column=1, sticky=tkinter.W)
        self.pao2 = tkinter.StringVar()
        self.PAO2 = ttk.Combobox(self.mainframe, textvariable=self.pao2)
        self.PAO2.grid(row=8, column=2, sticky=tkinter.W)
        self.PAO2['values'] = tuple(self.pao2_score.keys())
        self.pao2.set(self.PAO2['values'][3])
        self.PAO2.bind('<<ComboboxSelected>>', self.callback)

        # PH arterial ou HCO3
        ttk.Label(self.mainframe, text='PH arterial\nou HCO3: ').grid(row=9, column=1, sticky=tkinter.W)
        self.ph = tkinter.StringVar()
        self.PH = ttk.Combobox(self.mainframe, textvariable=self.ph)
        self.PH.grid(row=9, column=2, sticky=tkinter.W)
        self.PH['values'] = tuple(self.ph_score.keys())
        self.ph.set(self.PH['values'][3])
        self.PH.bind('<<ComboboxSelected>>', self.callback)

        # Na sérico
        ttk.Label(self.mainframe, text='Na+ sérico\n(meq/L): ').grid(row=10, column=1, sticky=tkinter.W)
        self.na = tkinter.StringVar()
        self.NA = ttk.Combobox(self.mainframe, textvariable=self.na)
        self.NA.grid(row=10, column=2, sticky=tkinter.W)
        self.NA['values'] = tuple(self.na_score.keys())
        self.na.set(self.NA['values'][3])
        self.NA.bind('<<ComboboxSelected>>', self.callback)

        # K sérico
        ttk.Label(self.mainframe, text='K+ sérico\n(meq/L): ').grid(row=11, column=1, sticky=tkinter.W)
        self.k = tkinter.StringVar()
        self.K = ttk.Combobox(self.mainframe, textvariable=self.k)
        self.K.grid(row=11, column=2, sticky=tkinter.W)
        self.K['values'] = tuple(self.k_score.keys())
        self.k.set(self.K['values'][3])
        self.K.bind('<<ComboboxSelected>>', self.callback)

        # Creatinina
        ttk.Label(self.mainframe, text='Cr sérica\n(meq/L): ').grid(row=12, column=1, sticky=tkinter.W)
        self.cr = tkinter.StringVar()
        self.CR = ttk.Combobox(self.mainframe, textvariable=self.cr)
        self.CR.grid(row=12, column=2, sticky=tkinter.W)
        self.CR['values'] = tuple(self.cr_score.keys())
        self.cr.set(self.CR['values'][1])
        self.CR.bind('<<ComboboxSelected>>', self.callback)

        # Hematócrito
        ttk.Label(self.mainframe, text='Hematócrito (%): ').grid(row=13, column=1, sticky=tkinter.W)
        self.ht = tkinter.StringVar()
        self.HT = ttk.Combobox(self.mainframe, textvariable=self.ht)
        self.HT.grid(row=13, column=2, sticky=tkinter.W)
        self.HT['values'] = tuple(self.ht_score.keys())
        self.ht.set(self.HT['values'][2])
        self.HT.bind('<<ComboboxSelected>>', self.callback)

        # Leucócitos
        ttk.Label(self.mainframe, text='Leucócitos(10^3/£gl): ').grid(row=14, column=1, sticky=tkinter.W)
        self.leuc = tkinter.StringVar()
        self.LEUC = ttk.Combobox(self.mainframe, textvariable=self.leuc)
        self.LEUC.grid(row=14, column=2, sticky=tkinter.W)
        self.LEUC['values'] = tuple(self.leuc_score.keys())
        self.leuc.set(self.LEUC['values'][2])
        self.LEUC.bind('<<ComboboxSelected>>', self.callback)

        # Glasgow
        ttk.Label(self.mainframe, text='Escala de coma\nde Glasgow: ').grid(row=15, column=1, sticky=tkinter.W)
        self.glasgow = tkinter.StringVar()
        self.GLASGOW = ttk.Combobox(self.mainframe, textvariable=self.glasgow)
        self.GLASGOW.grid(row=15, column=2, sticky=tkinter.W)
        self.GLASGOW['values'] = tuple(range(3, 16))
        self.glasgow.set(self.GLASGOW['values'][-1])
        self.GLASGOW.bind('<<ComboboxSelected>>', self.callback)

        # Problemas crônicos
        ttk.Label(self.mainframe, text='''Problemas Crônicos de Saúde(se presentes): 1) Cirrose confirmada
                  2) ICC classe IV da NYHA
                  3) DPOC grave: Hipercapnia,O2 Dependente, Hipertensão Pulmonar
                  4) Diálise Crônica
                  5) Imunocomprometido''').grid(row=16, column=2, sticky=tkinter.W)
        self.cronico = tkinter.StringVar()
        self.cronframe = tkinter.Frame(self.mainframe)
        self.cronframe.grid(row=17, column=1, columnspan=10, sticky=tkinter.EW)

        self.nenhuma = ttk.Radiobutton(self.cronframe, text='Nenhuma',
                                       variable=self.cronico, value='0', command=self.callback)
        self.nao_cirurgico = ttk.Radiobutton(self.cronframe, text='Não-Cirúrgico',
                                             variable=self.cronico, value='5', command=self.callback)
        self.cir_emerg = ttk.Radiobutton(self.cronframe, text='Cirurgia de Emergência',
                                         variable=self.cronico, value='5 ', command=self.callback)
        self.cir_elet = ttk.Radiobutton(self.cronframe, text='Cirurgia Eletiva',
                                        variable=self.cronico, value='2', command=self.callback)
        self.nenhuma.grid(row=1, column=1, sticky=tkinter.W)
        self.nao_cirurgico.grid(row=1, column=2, sticky=tkinter.W)
        self.cir_emerg.grid(row=1, column=3, sticky=tkinter.W)
        self.cir_elet.grid(row=1, column=4, sticky=tkinter.W)
        self.cronico.set('0')

        # Registro
        ttk.Label(self.mainframe, text='Registro: ').grid(row=4, column=4, sticky=tkinter.W)
        self.registro = tkinter.StringVar()
        self.reg_entry = ttk.Combobox(self.mainframe, width=5, textvariable=self.registro)
        self.reg_entry.grid(row=4, column=5, sticky=tkinter.W)
        self.reg_entry['values'] = self.list_id(self.db)
        self.reg_entry.bind('<<ComboboxSelected>>', self.abrir_id)

        # Resultado
        self.resultado = tkinter.StringVar()
        ttk.Label(self.cronframe, text='Resultado: ', font="Verdana 20 bold").grid(row=1, column=5, sticky=tkinter.W)
        self.LABEL = ttk.Label(self.cronframe, text=self.resultado.get(), font="Verdana 20 bold")
        self.LABEL.grid(row=1, column=6, sticky=tkinter.W)

        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=3, pady=3)

        for child in self.toolbar.winfo_children():
            child.grid_configure(padx=2, pady=3)

        self.callback()

    def __del__(self):
        if self.db is not None:
            self.db.close()

    def connect(self, filename):
        create = not os.path.exists(filename)
        db = sqlite3.connect(filename)
        if create:
            cursor = db.cursor()
            cursor.execute("CREATE TABLE pacientes ("
                           "id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, "
                           "nome TEXT NOT NULL, "
                           "sexo TEXT, "
                           "dia_nasc TEXT, "
                           "mes_nasc TEXT, "
                           "ano_nasc TEXT, "
                           "temperatura TEXT, "
                           "pam TEXT, "
                           "fc TEXT, "
                           "fr TEXT, "
                           "pao2 TEXT, "
                           "ph TEXT, "
                           "na TEXT, "
                           "k TEXT, "
                           "cr TEXT, "
                           "ht TEXT, "
                           "leuc TEXT, "
                           "glasgow TEXT, "
                           "cronico TEXT, "
                           "resultado TEXT)")
            db.commit()
        return db

    def list_pac(self, db):
        lista = []
        cursor = db.cursor()
        cursor.execute("SELECT nome FROM pacientes ORDER BY nome")
        for record in cursor:
            lista.append(record[0])
        return tuple(lista)

    def list_id(self, db):
        lista = []
        cursor = db.cursor()
        cursor.execute("SELECT id FROM pacientes ORDER BY id")
        for fields in cursor:
            lista.append(fields[0])
        return tuple(lista)

    def pac_count(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM pacientes")
        return cursor.fetchone()[0]

    def find_pac_id(self, nome):
        cursor = self.db.cursor()
        cursor.execute('SELECT nome, id FROM pacientes '
                       'WHERE nome=?',
                       (nome, ))
        records = cursor.fetchall()
        if len(records) != 1:
            return None
        else:
            return records[0][2]

    def copiar(self, *ignore):
        w = self.focus_get()
        w.event_generate("<<Copy>>")

    def colar(self, *ignore):
        w = self.focus_get()
        w.event_generate("<<Paste>>")

    def recortar(self, *ignore):
        w = self.focus_get()
        w.event_generate("<<Cut>>")

    def sobre(self, *ignore):
        messagebox.showinfo(message='Calculadora Score Apache-II versão 0.10', title='Sobre')

    def mortalidade(self, *ignore):
        messagebox.showinfo(message='0-4 pontos: 4% não op/ 1% pós-op\n' +
                                    '5-9 pontos: 8% não op/ 3% pós-op\n' +
                                    '10-14 pontos: 15% não op/ 7% pós-op\n' +
                                    '15-19 pontos: 24% não op/ 12% pós-op\n' +
                                    '20-24 pontos: 40% não op/ 30% pós-op\n' +
                                    '25-29 pontos: 55% não op/ 35% pós-op\n' +
                                    '30-34 pontos: 73% mortalidade geral\n' +
                                    '35-100 pontos: 85% não op/ 88% pós-op', title='Pontos x Mortalidade')

    def sair(self, event=None):
        if self.okayToContinue():
            self.destroy()

    def blank(self, *ignore):
        self.nome.set('')
        self.sexo.set(None)
        self.dia_nasc.set('01')
        self.mes_nasc.set('Janeiro')
        self.ano_nasc.set('1980')
        self.temperatura.set(self.temp['values'][4])
        self.pam.set(self.PA['values'][2])
        self.fc.set(self.FREQ['values'][3])
        self.fr.set(self.FR['values'][3])
        self.pao2.set(self.PAO2['values'][3])
        self.ph.set(self.PH['values'][3])
        self.na.set(self.NA['values'][3])
        self.k.set(self.K['values'][3])
        self.cr.set(self.CR['values'][1])
        self.ht.set(self.HT['values'][2])
        self.leuc.set(self.LEUC['values'][2])
        self.glasgow.set(self.GLASGOW['values'][-1])
        self.cronico.set('0')
        self.registro.set('')

        self.name_entry['values'] = self.list_pac(self.db)
        self.reg_entry['values'] = self.list_id(self.db)
        self.callback()

    def novo(self, *ignore):
        reply = messagebox.askyesno('Novo',
                                    'Deseja salvar alterações para o paciente {0}?'.format(self.nome.get()), parent=self)
        nome = self.nome.get()
        if not reply:
            self.blank()
        elif reply and len(nome) == 0:
            messagebox.showwarning(title='Atenção', message='É obrigatório preencher o nome')
            return
        else:
            self.salvar(self)
            self.blank()

    def salvar(self, *ignore):
        nome = self.nome.get()
        if not nome:
            messagebox.showwarning(title='Atenção', message='É obrigatório preencher o nome')
            return
        sexo = self.sexo.get()
        dia_nasc = self.dia_nasc.get()
        mes_nasc = self.mes_nasc.get()
        ano_nasc = self.ano_nasc.get()
        temperatura = self.temperatura.get()
        pam = self.pam.get()
        fc = self.fc.get()
        fr = self.fr.get()
        pao2 = self.pao2.get()
        ph = self.ph.get()
        na = self.na.get()
        k = self.k.get()
        cr = self.cr.get()
        ht = self.ht.get()
        leuc = self.leuc.get()
        glasgow = self.glasgow.get()
        cronico = self.cronico.get()
        resultado = self.resultado.get()

        identity = self.registro.get() if len(self.registro.get()) != 0 else None

        if identity is None:
            cursor = self.db.cursor()
            cursor.execute("INSERT INTO pacientes "
                           "(nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura, pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado) "
                           "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura,
                            pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado))
            self.db.commit()
        else:
            cursor = self.db.cursor()
            cursor.execute("UPDATE pacientes SET nome=:nome, sexo=:sexo, dia_nasc=:dia_nasc, mes_nasc=:mes_nasc, "
                           "ano_nasc=:ano_nasc, temperatura=:temperatura, pam=:pam, fc=:fc, fr=:fr, pao2=:pao2, ph=:ph, na=:na, "
                           "k=:k, cr=:cr, ht=:ht, leuc=:leuc, glasgow=:glasgow, cronico=:cronico, resultado=:resultado "
                           "WHERE id=:identity", locals())
            self.db.commit()

        self.name_entry['values'] = self.list_pac(self.db)
        self.reg_entry['values'] = self.list_id(self.db)

    def remover(self, *ignore):
        reply = messagebox.askyesno('Remover',
                                    'Deseja remover o paciente atual do Banco de Dados?', parent=self)

        if not reply:
            return
        nome = self.nome.get()
        reg = self.registro.get()
        identity = reg if len(reg) != 0 else self.find_pac_id(nome)
        if identity:
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM pacientes WHERE id=?", (identity,))
            self.db.commit()
            self.blank()
        else:
            messagebox.showwarning(message='Impossível Remover o Paciente. \nFavor Selecionar o Número do Registro', title='Atenção')

    def sair(self, event=None):
        if self.okayToContinue():
            self.destroy()

    def abrir_nome(self, *ignore):
        nome = self.nome.get()
        cursor = self.db.cursor()
        cursor.execute('SELECT nome, id FROM pacientes '
                       'WHERE nome=? ORDER BY nome',
                       (nome, ))
        records = cursor.fetchall()
        if len(records) > 1:
            ids = []
            for i in range(len(records)):
                ids.append(str(records[i][1]))
            messagebox.showinfo(message='Há mais de um paciente com o nome {0}.\nRegistros: ({1}) \nTente abrir pelo número do registro'
                                .format(nome, ', '.join(ids)), title='Atenção')
        else:
            self.registro.set(records[0][1])
            self.abrir_id()

    def abrir_id(self, *ignore):
        cursor = self.db.cursor()
        cursor.execute("SELECT nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura, pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado "
                       "FROM pacientes "
                       "WHERE id=?", (self.registro.get(),))

        nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura, pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado = cursor.fetchone()
        self.nome.set(nome)
        self.sexo.set(sexo)
        self.dia_nasc.set(dia_nasc)
        self.mes_nasc.set(mes_nasc)
        self.ano_nasc.set(ano_nasc)
        self.temperatura.set(temperatura)
        self.pam.set(pam)
        self.fc.set(fc)
        self.fr.set(fr)
        self.pao2.set(pao2)
        self.ph.set(ph)
        self.na.set(na)
        self.k.set(k)
        self.cr.set(cr)
        self.ht.set(ht)
        self.leuc.set(leuc)
        self.glasgow.set(glasgow)
        self.cronico.set(cronico)

        self.name_entry['values'] = self.list_pac(self.db)
        self.reg_entry['values'] = self.list_id(self.db)
        self.callback()

    def okayToContinue(self):
        reply = messagebox.askyesnocancel(
                   "Saída",
                   "Deseja salvar as alterações antes de sair?", parent=self)
        if reply is None:
            return False
        elif reply and len(self.nome.get()) > 0:
            self.salvar(self)
            return True
        else:
            return True

    def show_mouse_menu(self, e):
        w = e.widget
        self.MENUmouse.entryconfigure("Copiar", command=lambda: w.event_generate("<<Copy>>"))
        self.MENUmouse.entryconfigure("Colar", command=lambda: w.event_generate("<<Paste>>"))
        self.MENUmouse.entryconfigure("Recortar", command=lambda: w.event_generate("<<Cut>>"))
        self.MENUmouse.tk.call("tk_popup", self.MENUmouse, e.x_root, e.y_root)

    def callback(self, *ignore):
        self.res_buffer = 0
        try:
            self.mes_idade = int(self.mes['values'].index(self.mes_nasc.get())) + 1
            self.n = datetime.date.today() - datetime.date(int(self.ano_nasc.get()), self.mes_idade, int(self.dia_nasc.get()))
            self.idade.set(str(self.n.days / 365.25)[:5])
        except:
            self.idade.set('Inválido')

        self.res_buffer += self.temp_score[self.temperatura.get()]
        self.res_buffer += self.pa_score[self.pam.get()]
        self.res_buffer += self.fc_score[self.fc.get()]
        self.res_buffer += self.fr_score[self.fr.get()]
        self.res_buffer += self.pao2_score[self.pao2.get()]
        self.res_buffer += self.ph_score[self.ph.get()]
        self.res_buffer += self.na_score[self.na.get()]
        self.res_buffer += self.k_score[self.k.get()]
        self.res_buffer += self.cr_score[self.cr.get()]
        self.res_buffer += self.ht_score[self.ht.get()]
        self.res_buffer += self.leuc_score[self.leuc.get()]
        self.res_buffer += (15 - int(self.glasgow.get()))
        self.res_buffer += int(self.cronico.get())

        if self.idade.get() == 'Inválido':
            self.resultado.set('Inválido')
            self.LABEL.config(text=self.resultado.get())
            return
        elif floor(float(self.idade.get())) >= 75:
            self.res_buffer += 6
        elif 65 <= floor(float(self.idade.get())) <= 74:
            self.res_buffer += 5
        elif 55 <= floor(float(self.idade.get())) <= 64:
            self.res_buffer += 3
        elif 45 <= floor(float(self.idade.get())) <= 54:
            self.res_buffer += 2
        elif floor(float(self.idade.get())) <= 44:
            pass

        self.resultado.set(self.res_buffer)
        self.LABEL.config(text=self.resultado.get())

    def importar_db(self, *ignore):
        reply = messagebox.askyesno(title='Info', message='Esta ação irá apagar o banco de dados atual e importar um novo XML. Deseja continuar?')
        if not reply:
            return

        options = {}
        options['filetypes'] = [('Arquivos XML', '.xml'), ('Todos Arquivos', '.*')]
        options['initialfile'] = 'patients.xml'
        fileName = askopenfilename(**options)
        if not fileName:
            return

        try:
            tree = xml.etree.ElementTree.parse(fileName)
        except (EnvironmentError, xml.parsers.expat.ExpatError, xml.etree.ElementTree.ParseError) as err:
            messagebox.showwarning(title='Erro', message='ERRO: {0}. Não foi possível importar o banco de dados'.format(err))
            return

        cursor = self.db.cursor()
        cursor.execute("DELETE FROM pacientes")

        for element in tree.findall("pac"):
            try:
                nome = element.text.strip()
                sexo = element.get("sexo")
                dia_nasc = element.get("dia_nasc")
                mes_nasc = element.get("mes_nasc")
                ano_nasc = element.get("ano_nasc")
                temperatura = element.get("temperatura")
                pam = element.get("pam")
                fc = element.get("fc")
                fr = element.get("fr")
                pao2 = element.get("pao2")
                ph = element.get("ph")
                na = element.get("na")
                k = element.get("k")
                cr = element.get("cr")
                ht = element.get("ht")
                leuc = element.get("leuc")
                glasgow = element.get("glasgow")
                cronico = element.get("cronico")
                resultado = element.get("resultado")
                cursor.execute("INSERT INTO pacientes "
                               "(nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura, pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado) "
                               "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura,
                                pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado))
            except ValueError as err:
                self.db.rollback()
                messagebox.showwarning(title='Erro', message='ERRO: {0}. Não foi possível importar o banco de dados'.format(err))
                break
        else:
            self.db.commit()
            self.name_entry['values'] = self.list_pac(self.db)
            self.reg_entry['values'] = self.list_id(self.db)
            messagebox.showinfo(title='Info', message='Arquivo XML importado com sucesso. Foram importados {0} pacientes'.format(self.pac_count(self.db)))
            self.blank()

    def exportar_db(self, *ignore):
        options = {}
        options['filetypes'] = [('Arquivos XML', '.xml'), ('Todos Arquivos', '.*')]
        options['initialfile'] = 'patients.xml'
        fileName = asksaveasfilename(**options)
        if not fileName:
            return

        cursor = self.db.cursor()
        cursor.execute("SELECT nome, sexo, dia_nasc, mes_nasc, ano_nasc, temperatura, pam, fc, fr, pao2, ph, na, k, cr, ht, leuc, glasgow, cronico, resultado "
                       "FROM pacientes "
                       "ORDER BY nome ")

        try:
            with open(fileName, mode="w", encoding="UTF-8") as fh:
                fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                fh.write("<pacientes>\n")
                for record in cursor:
                    fh.write('  <pac sexo={0} dia_nasc={1} '
                             'mes_nasc={2} ano_nasc={3} temperatura={4} '
                             'pam={5} fc={6} fr={7} pao2={8} '
                             'ph={9} na={10} k={11} '
                             'cr={12} ht={13} leuc={14} '
                             'glasgow={15} cronico={16} resultado={17}>'.format(xml.sax.saxutils.quoteattr(record[1]),
                                                                                xml.sax.saxutils.quoteattr(record[2]),
                                                                                xml.sax.saxutils.quoteattr(record[3]),
                                                                                xml.sax.saxutils.quoteattr(record[4]),
                                                                                xml.sax.saxutils.quoteattr(record[5]),
                                                                                xml.sax.saxutils.quoteattr(record[6]),
                                                                                xml.sax.saxutils.quoteattr(record[7]),
                                                                                xml.sax.saxutils.quoteattr(record[8]),
                                                                                xml.sax.saxutils.quoteattr(record[9]),
                                                                                xml.sax.saxutils.quoteattr(record[10]),
                                                                                xml.sax.saxutils.quoteattr(record[11]),
                                                                                xml.sax.saxutils.quoteattr(record[12]),
                                                                                xml.sax.saxutils.quoteattr(record[13]),
                                                                                xml.sax.saxutils.quoteattr(record[14]),
                                                                                xml.sax.saxutils.quoteattr(record[15]),
                                                                                xml.sax.saxutils.quoteattr(record[16]),
                                                                                xml.sax.saxutils.quoteattr(record[17]),
                                                                                xml.sax.saxutils.quoteattr(record[18])))
                    fh.write(xml.sax.saxutils.escape(record[0]))
                    fh.write("</pac>\n")
                fh.write("</pacientes>\n")
            messagebox.showinfo(title='Info', message='Arquivo XML exportado com sucesso')
        except EnvironmentError as err:
            messagebox.showwarning(title='Erro', message='ERRO: {0}. Não foi possível exportar o banco de dados'.format(err))

if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()
