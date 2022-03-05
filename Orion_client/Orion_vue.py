# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import ttk
from tkinter.simpledialog import *
from tkinter.messagebox import *
from helper import Helper as hlp
import math

import random
import os,os.path,sys


class Vue():
    def __init__(self,parent,urlserveur,monnom,testdispo):
        self.parent=parent
        self.root=Tk()
        self.root.title("Je suis "+monnom)
        self.monnom=monnom
        # attributs
        self.cadrechaton=0
        self.textchat=""
        self.infohud={}
        self.tailleminicarte=220

        self.zoom=1
        self.maselection=None

        self.cadreactif=None
        # # objet pour cumuler les manipulations du joueur pour generer une action de jeu
        self.action=Action(self)

        # cadre principal de l'application
        self.cadreapp=Frame(self.root,width=500,height=400,bg="red")
        self.cadreapp.pack(expand=1,fill=BOTH)

        # # un dictionnaire pour conserver les divers cadres du jeu, creer plus bas
        self.cadres={}
        self.creer_cadres(urlserveur,monnom,testdispo)
        self.changer_cadre("splash")
        # PROTOCOLE POUR INTERCEPTER LA FERMETURE DU ROOT - qui termine l'application
        #self.root.protocol("WM_DELETE_WINDOW", self.demander_abandon)

        # # sera charge apres l'initialisation de la partie, contient les donnees pour mettre l'interface a jour
        self.modele=None
        # # variable pour suivre le trace du multiselect
        self.debut_selection=[]
        self.selecteuractif=None
        # # images des assets, definies dans le modue loadeurimages
        #self.images=chargerimages()
        #self.gifs=chargergifs()

    def demander_abandon(self):
        rep=askokcancel("Vous voulez vraiment quitter?")
        if rep:
            self.root.after(500, self.root.destroy)

####### INTERFACES GRAPHIQUES
    def changer_cadre(self,nomcadre: str):
        cadre=self.cadres[nomcadre]
        if self.cadreactif:
            self.cadreactif.pack_forget()
        self.cadreactif=cadre
        self.cadreactif.pack(expand=1,fill=BOTH)

    ###### LES CADRES ############################################################################################
    def creer_cadres(self, urlserveur: str, monnom: str, testdispo: str):
        self.cadres["splash"] = self.creer_cadre_splash(urlserveur, monnom, testdispo)
        self.cadres["lobby"] = self.creer_cadre_lobby()
        #self.cadres["jeu"] = self.creer_cadre_jeu()

    # le splash (ce qui 'splash' à l'écran lors du démarrage)
    # sera le cadre visuel initial lors du lancement de l'application
    def creer_cadre_splash(self, urlserveur: str, monnom: str, testdispo: str) -> Frame:
        self.cadresplash = Frame(self.cadreapp)
        # un canvas est utilisé pour 'dessiner' les widgets de cette fenêtre voir 'create_window' plus bas
        self.canevassplash = Canvas(self.cadresplash, width=600, height=480, bg="pink")
        self.canevassplash.pack()

        # creation ds divers widgets (champ de texte 'Entry' et boutons cliquables (Button)
        self.etatdujeu = Label(text=testdispo, font=("Arial", 18), borderwidth=2, relief=RIDGE)
        self.nomsplash = Entry(font=("Arial", 14))
        self.urlsplash = Entry(font=("Arial", 14))
        self.btnurlconnect = Button(text="Connecter", font=("Arial", 12), command=self.connecter_serveur)
        # on insère les infos par défaut (nom url) et reçu au démarrage (dispo)
        self.nomsplash.insert(0, monnom)
        self.urlsplash.insert(0, urlserveur)
        # on les place sur le canevassplash
        self.canevassplash.create_window(320, 100, window=self.etatdujeu, width=400, height=30)
        self.canevassplash.create_window(320, 200, window=self.nomsplash, width=400, height=30)
        self.canevassplash.create_window(240, 250, window=self.urlsplash, width=200, height=30)
        self.canevassplash.create_window(420, 250, window=self.btnurlconnect, width=100, height=30)
        # les boutons d'actions
        self.btncreerpartie = Button(text="Creer partie", font=("Arial", 12), state=DISABLED, command=self.creer_partie)
        self.btninscrirejoueur = Button(text="Inscrire joueur", font=("Arial", 12), state=DISABLED, command=self.inscrire_joueur)
        self.btnreset = Button(text="Reinitialiser partie", font=("Arial", 9), state=DISABLED, command=self.reset_partie)

        # on place les autres boutons
        self.canevassplash.create_window(420, 350, window=self.btncreerpartie, width=200, height=30)
        self.canevassplash.create_window(420, 400, window=self.btninscrirejoueur, width=200, height=30)
        self.canevassplash.create_window(420, 450, window=self.btnreset, width=200, height=30)

        # on retourne ce cadre pour l'insérer dans le dictionnaires des cadres
        return self.cadresplash

    def connecter_serveur(self):
        self.btninscrirejoueur.config(state=NORMAL)
        self.btncreerpartie.config(state=NORMAL)
        self.btnreset.config(state=NORMAL)
        url_serveur=self.urlsplash.get()
        self.parent.connecter_serveur(url_serveur)


    ######## le lobby (où on attend les inscriptions)
    def creer_cadre_lobby(self):
        # le cadre lobby, pour isncription des autres joueurs, remplace le splash
        self.cadrelobby=Frame(self.cadreapp)
        self.canevaslobby=Canvas(self.cadrelobby,width=640,height=480,bg="lightblue")
        self.canevaslobby.pack()
        # widgets du lobby
        # un listbox pour afficher les joueurs inscrit pour la partie à lancer
        self.listelobby=Listbox(borderwidth=2,relief=GROOVE)

        # bouton pour lancer la partie, uniquement accessible à celui qui a creer la partie dans le splash
        self.btnlancerpartie=Button(text="Lancer partie",state=DISABLED,command=self.lancer_partie)
        # affichage des widgets dans le canevaslobby (similaire au splash)
        self.canevaslobby.create_window(440,240,window=self.listelobby,width=200,height=400)
        self.canevaslobby.create_window(200,400,window=self.btnlancerpartie,width=100,height=30)
        # on retourne ce cadre pour l'insérer dans le dictionnaires des cadres
        return self.cadrelobby

    def initialiser_avec_modele(self,modele):
        self.nom=self.parent.monnom
        self.modele=modele
        self.cadrepartie=Frame(self.cadreapp,width=600,height=200, bg="yellow")
        self.cadrejeu=Frame(self.cadrepartie,width=600,height=200,bg="teal")

        self.scrollX=Scrollbar(self.cadrejeu,orient=HORIZONTAL)
        self.scrollY=Scrollbar(self.cadrejeu,orient=VERTICAL)
        self.canevas=Canvas(self.cadrejeu,width=800,height=600,scrollregion=(0,0,modele.largeur,modele.hauteur),
                            xscrollcommand = self.scrollX.set,
                            yscrollcommand = self.scrollY.set,bg="grey11")

        self.scrollX.config(command=self.canevas.xview)
        self.scrollY.config(command=self.canevas.yview)

        self.canevas.grid(column=0,row=0,sticky=W+E+N+S)
        self.scrollX.grid(column=0,row=1,sticky=W+E)
        self.scrollY.grid(column=1,row=0,sticky=N+S)

        self.cadrejeu.columnconfigure(0,weight=1)
        self.cadrejeu.rowconfigure(0,weight=1)

        self.canevas.bind("<Button>",self.cliquecosmos)

        self.cadrejeu.pack(side=LEFT,expand=1,fill=BOTH)

        self.cadreoutils=Frame(self.cadrepartie,width=200,height=200,bg="darkgrey")
        self.cadreoutils.pack(side=LEFT,fill=Y)

        self.cadreinfo=Frame(self.cadreoutils,width=200,height=200,bg="darkgrey")
        self.cadreinfo.pack(fill=Y)
        self.cadreinfogen=Frame(self.cadreinfo,width=200,height=200,bg="grey50")
        self.cadreinfogen.pack()
        self.labid=Label(self.cadreinfogen,text=self.nom,fg=modele.joueurs[self.nom].couleur)
        self.labid.bind("<Button>",self.afficherplanemetemere)
        self.labid.pack()
        self.cadreinfochoix=Frame(self.cadreinfo,height=200,width=200,bg="grey30")
        self.cadreinfochoix.pack()
        self.btncreervaisseau=Button(self.cadreinfo,text="Vaisseau")
        self.btncreervaisseau.bind("<Button>",self.creervaisseau)
        self.btncreercargo=Button(self.cadreinfo,text="Cargo")
        self.btncreercargo.bind("<Button>",self.creervaisseau)
        self.lbselectecible=Label(self.cadreinfo,text="Choisir cible",bg="darkgrey")


        self.cadreminimap=Frame(self.cadreoutils,height=200,width=200,bg="black")
        self.canevasMini=Canvas(self.cadreminimap,width=200,height=200,bg="pink")
        self.canevasMini.bind("<Button>",self.moveCanevas)
        self.canevasMini.pack()
        self.cadreminimap.pack()

        self.afficherdecor(modele)

        self.cadres["jeu"] = self.cadrepartie


        self.canevas.bind("<Shift-Button-3>", self.calc_objets)


    def connecter_event(self):
        # actions de clics sur la carte
        self.canevas.bind("<Button-1>", self.annuler_action)
        self.canevas.bind("<Button-2>", self.indiquer_position)
        self.canevas.bind("<Button-3>", self.construire_batiment)
        # faire une multiselection
        self.canevas.bind("<Shift-Button-1>", self.debuter_multiselection)
        self.canevas.bind("<Shift-B1-Motion>", self.afficher_multiselection)
        self.canevas.bind("<Shift-ButtonRelease-1>", self.terminer_multiselection)
        # scroll avec roulette
        self.canevas.bind("<MouseWheel>", self.defiler_vertical)
        self.canevas.bind("<Control-MouseWheel>", self.defiler_horizon)

        # # acgtions liées aux objets dessinés par tag
        # self.canevas.tag_bind("batiment", "<Button-1>", self.creer_entite)
        # self.canevas.tag_bind("perso", "<Button-1>", self.ajouter_selection)
        # self.canevas.tag_bind("arbre", "<Button-1>", self.ramasser_ressource)
        # self.canevas.tag_bind("aureus", "<Button-1>", self.ramasser_ressource)
        # self.canevas.tag_bind("roche", "<Button-1>", self.ramasser_ressource)
        # self.canevas.tag_bind("baie", "<Button-1>", self.ramasser_ressource)
        # self.canevas.tag_bind("eau", "<Button-1>", self.ramasser_ressource)
        # self.canevas.tag_bind("daim", "<Button-1>", self.chasser_ressource)

    def calc_objets(self,evt):
        print("Univers = ",len(self.canevas.find_all()))

    def defiler_vertical(self, evt):
        rep = self.scrollV.get()[0]
        if evt.delta < 0:
            rep = rep + 0.01
        else:
            rep = rep - 0.01
        self.canevas.yview_moveto(rep)

    def defiler_horizon(self, evt):
        rep = self.scrollH.get()[0]
        if evt.delta < 0:
            rep = rep + 0.02
        else:
            rep = rep - 0.02
        self.canevas.xview_moveto(rep)

    ### cadre qui s'Affichera par-dessus le canevas de jeu pour l'aide
    def creer_aide(self):
        self.cadreaide=Frame(self.canevas)
        self.scrollVaide=Scrollbar(self.cadreaide,orient=VERTICAL)
        self.textaide=Text(self.cadreaide,width=50,height=10,
                            yscrollcommand = self.scrollVaide.set )
        self.scrollVaide.config(command = self.textaide.yview)
        self.textaide.pack(side=LEFT)
        self.scrollVaide.pack(side=LEFT,expand=1, fill=Y)
        fichieraide=open("aide.txt")
        monaide=fichieraide.read()
        fichieraide.close()
        self.textaide.insert(END, monaide)
        self.textaide.config(state=DISABLED)

    ### cadre qui affichera un chatbox
    def creer_chatter(self):
        self.cadrechat=Frame(self.canevas,bd=2,bg="orange")
        self.cadrechatlist=Frame(self.cadrechat)

        self.scrollVchat=Scrollbar(self.cadrechatlist,orient=VERTICAL)
        self.textchat=Listbox(self.cadrechatlist,width=30,height=6,
                            yscrollcommand = self.scrollVchat.set )
        self.scrollVchat.config(command = self.textchat.yview)
        self.textchat.pack(side=LEFT)
        self.scrollVchat.pack(side=LEFT,expand=1, fill=Y)
        self.textchat.delete(0, END)
        self.cadrechatlist.pack()
        # inscrire texte et choisir destinataire
        self.cadreparler=Frame(self.cadrechat,bd=2)
        self.joueurs=ttk.Combobox(self.cadreparler,
                                  values=list(self.modele.joueurs.keys()))
        self.entreechat=Entry(self.cadreparler,width=20)
        self.entreechat.bind("<Return>")#,self.action.envoyerchat)
        self.joueurs.pack(expand=1,fill=X)
        self.entreechat.pack(expand=1,fill=X)
        self.cadreparler.pack(expand=1,fill=X)

##### FONCTIONS DU SPLASH #########################################################################
    def creer_partie(self):
        nom=self.nomsplash.get()
        self.parent.creer_partie(nom)

    ###  FONCTIONS POUR SPLASH ET LOBBY INSCRIPTION pour participer a une partie
    def update_splash(self,etat):
        if "attente" in etat or "courante" in etat:
            self.btncreerpartie.config(state=DISABLED)
        if "courante" in etat:
            self.etatdujeu.config(text="Desole - partie encours !")
            self.btninscrirejoueur.config(state=DISABLED)
        elif "attente" in etat:
            self.etatdujeu.config(text="Partie en attente de joueurs !")
            self.btninscrirejoueur.config(state=NORMAL)
        elif "dispo" in etat:
            self.etatdujeu.config(text="Bienvenue ! Serveur disponible")
            self.btninscrirejoueur.config(state=DISABLED)
            self.btncreerpartie.config(state=NORMAL)
        else:
            self.etatdujeu.config(text="ERREUR - un probleme est survenu")

    ##### FONCTION DU LOBBY #############
    def update_lobby(self,dico):
        self.listelobby.delete(0,END)
        for i in dico:
            self.listelobby.insert(END,i[0])
        if self.parent.joueur_createur:
            self.btnlancerpartie.config(state=NORMAL)

    def inscrire_joueur(self):
        nom=self.nomsplash.get()
        urljeu=self.urlsplash.get()
        self.parent.inscrire_joueur(nom,urljeu)

    def lancer_partie(self):
        self.parent.lancer_partie()

    def reset_partie(self):
        rep=self.parent.reset_partie()


####################################################################################################
    def moveCanevas(self,evt):
        x=evt.x
        y=evt.y
        px=self.mod.largeur/x/100
        py=self.mod.hauteur/y/100
        self.canevas.xview(MOVETO,px)
        self.canevas.yview(MOVETO,py)
        print("SCROLL",px,py)

    def afficherdecor(self, mod):

        for i in range(len(mod.etoiles) * 50):
            x = random.randrange(int(mod.largeur))
            y = random.randrange(int(mod.hauteur))
            n = random.randrange(3) + 1
            col = random.choice(["LightYellow", "azure1", "pink"])
            self.canevas.create_oval(x, y, x + n, y + n, fill=col, tags=("fond",))

        for i in mod.etoiles:
            t = i.taille * self.zoom
            col = random.choice(["LightYellow", "azure1", "pink"])
            self.canevas.create_oval((i.x) - t,
                                     (i.y) - t,
                                     (i.x) + t,
                                     (i.y) + t,
                                     fill="grey80",
                                     outline=col,
                                     tags=(i.proprietaire, "etoile", str(i.id)))
        for i in mod.joueurs.keys():
            for j in mod.joueurs[i].etoilescontrolees:
                t = j.taille * self.zoom
                self.canevas.create_oval((j.x) - t,
                                         (j.y) - t,
                                         (j.x) + t,
                                         (j.y) + t,
                                         fill=mod.joueurs[i].couleur,
                                         tags=(j.proprietaire, "etoile", str(j.id), "possession"))
                print("MA PLANETE", j.x, j.y)
        # dessine IAs

        for i in mod.ias:
            for j in i.etoilescontrolees:
                t = j.taille * self.zoom
                self.canevas.create_oval((j.x) - t,
                                         (j.y) - t,
                                         (j.x) + t,
                                         (j.y) + t,
                                         fill=i.couleur,
                                         tags=(j.proprietaire, "etoile", str(j.id), "possession"))


    def afficherdecor1(self,mod):

        for i in range(len(mod.etoiles)*50):
            x=random.randrange(int(mod.largeur*self.zoom))
            y=random.randrange(int(mod.hauteur*self.zoom))
            n=random.randrange(3)+1
            col=random.choice(["LightYellow","azure1","pink"])
            self.canevas.create_oval(x,y,x+n,y+n,fill=col,tags=("fond",))

        for i in mod.etoiles:
            t=i.taille*self.zoom
            col=random.choice(["LightYellow","azure1","pink"])
            self.canevas.create_oval((i.x*self.zoom)-t,
                                     (i.y*self.zoom)-t,
                                     (i.x*self.zoom)+t,
                                     (i.y*self.zoom)+t,
                                     fill="grey80",
                                     outline=col,
                                     tags=(i.proprietaire,"etoile",str(i.id)))
        for i in mod.joueurs.keys():
            for j in mod.joueurs[i].etoilescontrolees:
                t=j.taille*self.zoom
                self.canevas.create_oval((j.x*self.zoom)-t,
                                         (j.y*self.zoom)-t,
                                         (j.x*self.zoom)+t,
                                         (j.y*self.zoom)+t,
                                         fill=mod.joueurs[i].couleur,
                                     tags=(j.proprietaire,"etoile",str(j.id),"possession"))
                print("MA PLANETE",j.x,j.y)
        # dessine IAs

        for i in mod.ias:
            for j in i.etoilescontrolees:
                t=j.taille*self.zoom
                self.canevas.create_oval((j.x*self.zoom)-t,
                                         (j.y*self.zoom)-t,
                                         (j.x*self.zoom)+t,
                                         (j.y*self.zoom)+t,
                                         fill=i.couleur,
                                     tags=(j.proprietaire,"etoile",str(j.id),"possession"))



        #self.afficher_afficher_jeu()
                
    def afficherplanemetemere(self,evt):
        print("HELLLLLLLO MERE PLANETE")
        j=self.modele.joueurs[self.nom]
        couleur=j.couleur
        x=j.etoilemere.x
        y=j.etoilemere.y
        t=10*self.zoom
        self.canevas.create_oval((x*self.zoom)-t,
                                 (y*self.zoom)-t,
                                 (x*self.zoom)+t,
                                 (y*self.zoom)+t,
                                 dash=(3,3),width=2,outline=couleur,
                                 tags=("etoilemere","marqueur"))


        x1=self.canevas.winfo_width()/2
        y1=self.canevas.winfo_height()/2

        pctx=(x-x1)/self.modele.largeur
        pcty=(y-y1)/self.modele.hauteur

        self.canevas.xview_moveto(pctx)
        self.canevas.yview_moveto(pcty)


    def creervaisseau(self,evt):
        type_vaisseau=evt.widget.cget("text")
        print("Creer vaisseau",type_vaisseau)
        self.parent.creer_vaisseau(type_vaisseau)
        self.maselection=None
        self.canevas.delete("marqueur")
        self.btncreervaisseau.pack_forget()
        self.btncreercargo.pack_forget()

    def afficher_jeu(self):
        mod = self.modele
        self.canevas.delete("artefact")

        if self.maselection != None:
            joueur = mod.joueurs[self.maselection[0]]
            if self.maselection[1] == "etoile":
                for i in joueur.etoilescontrolees:
                    if i.id == self.maselection[2]:
                        x = i.x
                        y = i.y
                        t = 10 * self.zoom
                        self.canevas.create_oval((x) - t,
                                                 (y) - t,
                                                 (x) + t,
                                                 (y) + t,
                                                 dash=(2, 2), outline=mod.joueurs[self.nom].couleur,
                                                 tags=("select", "marqueur"))
            elif self.maselection[1] == "flotte":
                for j in joueur.flotte:
                    for i in joueur.flotte[j]:
                        i=joueur.flotte[j][i]
                        if i.id == self.maselection[2]:
                            x = i.x
                            y = i.y
                            t = 10 * self.zoom
                            self.canevas.create_rectangle((x) - t,
                                                          (y) - t,
                                                          (x) + t,
                                                          (y) + t,
                                                          dash=(2, 2), outline=mod.joueurs[self.nom].couleur,
                                                          tags=("select", "marqueur"))


        for i in mod.joueurs.keys():
            i = mod.joueurs[i]
            for k in i.flotte:
                for j in i.flotte[k]:
                    j=i.flotte[k][j]
                    tailleF = j.taille * self.zoom
                    if k=="Vaisseau":
                        self.canevas.create_rectangle((j.x - tailleF),
                                                      (j.y - tailleF),
                                                      (j.x + tailleF),
                                                      (j.y + tailleF),
                                                      fill=i.couleur,
                                                      tags=(j.proprietaire, "flotte", str(j.id), "artefact"))
                    else:
                        self.canevas.create_oval((j.x - tailleF),
                                                      (j.y - tailleF),
                                                      (j.x + tailleF),
                                                      (j.y + tailleF),
                                                      fill=i.couleur,
                                                      tags=(j.proprietaire, "flotte", str(j.id), "artefact"))

        for i in mod.ias:
            for j in i.flotte["Vaisseau"]:
                j=i.flotte["Vaisseau"][j]

                x1, y1 = hlp.getAngledPoint(j.ang, j.taille / 2, j.x, j.y)

                x2, y2 = hlp.getAngledPoint(j.ang - math.pi, j.taille / 2, j.x, j.y)
                self.canevas.create_line(x1, y1, x2, y2, width=3, fill=i.couleur,
                                         tags=(j.proprietaire, "flotte", str(j.id), "artefact"))


    def afficher_jeu1(self):
        mod=self.modele
        self.canevas.delete("artefact")
        
        if self.maselection!=None:
            joueur=mod.joueurs[self.maselection[0]]
            if self.maselection[1]=="etoile":
                for i in joueur.etoilescontrolees:
                    if i.id == self.maselection[2]:
                        x=i.x
                        y=i.y
                        t=10*self.zoom
                        self.canevas.create_oval((x*self.zoom)-t,
                                                 (y*self.zoom)-t,
                                                 (x*self.zoom)+t,
                                                 (y*self.zoom)+t,
                                                 dash=(2,2),outline=mod.joueurs[self.nom].couleur,
                                                 tags=("select","marqueur"))
            elif self.maselection[1]=="flotte":
                for i in joueur.flotte:
                    if i.id == self.maselection[2]:
                        x=i.x
                        y=i.y
                        t=10*self.zoom
                        self.canevas.create_rectangle((x*self.zoom)-t,
                                                      (y*self.zoom)-t,
                                                      (x*self.zoom)+t,
                                                      (y*self.zoom)+t,
                                                      dash=(2,2),outline=mod.joueurs[self.nom].couleur,
                                                      tags=("select","marqueur"))
            
        tailleF=5*self.zoom
        for i in mod.joueurs.keys():
            i=mod.joueurs[i]
            for j in i.flotte:
                self.canevas.create_rectangle((j.x-tailleF)*self.zoom,
                                              (j.y-tailleF)*self.zoom,
                                              (j.x+tailleF)*self.zoom,
                                              (j.y+tailleF)*self.zoom,
                                              fill=i.couleur,
                                              tags=(j.proprietaire,"flotte",str(j.id),"artefact"))
                
        for i in mod.ias:
            for j in i.flotte:
                # self.canevas.create_rectangle((j.x-tailleF)*self.zoom,
                #                               (j.y-tailleF)*self.zoom,
                #                               (j.x+tailleF)*self.zoom,
                #                               (j.y+tailleF)*self.zoom,
                #                               fill=i.couleur,
                #                      tags=(j.proprietaire,"flotte",str(j.id),"artefact"))

                x1, y1 = hlp.getAngledPoint(j.ang, j.taille/2, j.x, j.y)

                x2, y2 = hlp.getAngledPoint(j.ang-math.pi, j.taille/2, j.x, j.y)
                self.canevas.create_line(x1,y1,x2,y2, width=3, fill=i.couleur,
                                     tags=(j.proprietaire,"flotte",str(j.id),"artefact"))


    def cliquecosmos(self,evt):
        self.btncreervaisseau.pack_forget()
        self.btncreercargo.pack_forget()
        t=self.canevas.gettags(CURRENT)
        if t and t[0]==self.nom:
            #self.maselection=self.canevas.find_withtag(CURRENT)#[0]
            self.maselection=[self.nom,t[1],t[2]]  #self.canevas.find_withtag(CURRENT)#[0]
            print(self.maselection)
            if t[1] == "etoile":
                self.montreetoileselection()
            elif t[1] == "flotte":
                self.montreflotteselection()
        elif "etoile" in t and t[0]!=self.nom:
            if self.maselection:
                pass # attribuer cette etoile a la cible de la flotte selectionne
                self.parent.ciblerflotte(self.maselection[2],t[2])
            print("Cette etoile ne vous appartient pas - elle est a ",t[0])
            self.maselection=None
            self.lbselectecible.pack_forget()
            self.canevas.delete("marqueur")
        else:
            print("Region inconnue")
            self.maselection=None
            self.lbselectecible.pack_forget()
            self.canevas.delete("marqueur")
            
    def montreetoileselection(self):
        self.btncreervaisseau.pack()
        self.btncreercargo.pack()

    def montreflotteselection(self):
        self.lbselectecible.pack()
    
    def afficherartefacts(self,joueurs):
        pass #print("ARTEFACTS de ",self.nom)

        ##### ACTIONS DU JOUEUR #######################################################################

    def annuler_action(self, evt):
        mestags = self.canevas.gettags(CURRENT)
        if not mestags:
            self.canevasaction.delete(self.action.widgetsactifs)
            if self.action.btnactif:
                self.action.btnactif.config(bg="SystemButtonFace")
            self.action = Action(self)

    def fermer_chat(self):
        self.textchat = None
        self.fenchat.destroy()

    def ajouter_selection(self, evt):
        mestags = self.canevas.gettags(CURRENT)
        if self.parent.monnom == mestags[1]:
            if "Ouvrier" == mestags[4]:
                self.action.persochoisi.append(mestags[2])
                self.action.afficher_commande_perso()
            ######
            else:
                self.action.persochoisi.append(mestags[2])

    def indiquer_position(self,evt):
        tag=self.canevas.gettags(CURRENT)
        if not tag and self.action.persochoisi:
            x,y=(self.canevas.canvasx(evt.x),self.canevas.canvasy(evt.y))
            self.action.position=[x,y]
            self.action.deplacer()


    def construire_batiment(self,evt):
        mestags=self.canevas.gettags(CURRENT)
        if not mestags and self.action.persochoisi and self.action.prochaineaction:
            pos=(self.canevas.canvasx(evt.x),self.canevas.canvasy(evt.y))
            self.action.construire_batiment(pos)

    # Methodes pour multiselect#########################################################
    def debuter_multiselection(self,evt):
        self.debutselect=(self.canevas.canvasx(evt.x),self.canevas.canvasy(evt.y))
        x1,y1=(self.canevas.canvasx(evt.x),self.canevas.canvasy(evt.y))
        self.selecteuractif=self.canevas.create_rectangle(x1,y1,x1+1,y1+1,outline="red",width=2,
                                                          dash=(2,2),tags=("","selecteur","","artefact"))


    def afficher_multiselection(self,evt):
        if self.debutselect:
            x1,y1=self.debutselect
            x2,y2=(self.canevas.canvasx(evt.x),self.canevas.canvasy(evt.y))
            self.canevas.coords(self.selecteuractif,x1,y1,x2,y2)

    def terminer_multiselection(self,evt):
        if self.debutselect:
            x1,y1=self.debutselect
            x2,y2=(self.canevas.canvasx(evt.x),self.canevas.canvasy(evt.y))
            self.debutselect=[]
            objchoisi=(list(self.canevas.find_enclosed(x1,y1,x2,y2)))
            for i in objchoisi:
                if self.parent.monnom not in self.canevas.gettags(i):
                    objchoisi.remove(i)
                else:
                    self.action.persochoisi.append(self.canevas.gettags(i)[2])

            if self.action.persochoisi:
                self.action.afficher_commande_perso()
            self.canevas.delete("selecteur")
    ### FIN du multiselect


#####################################################################
# Singleton (mais pas automatique) sert a conserver les manipulations du joueur pour demander une action
######   CET OBJET SERVIRA À CONSERVER LES GESTES ET INFOS REQUISES POUR PRODUIRE UNE ACTION DE JEU
class Action():
    def __init__(self,parent):
        self.parent=parent
        self.persochoisi=[]
        self.ciblechoisi=None
        self.position=[]
        self.btnactif=None  # le bouton choisi pour creer un batiment
        self.prochaineaction=None # utiliser pour les batiments seulement
        self.widgetsactifs=[]
        self.chaton=0
        self.aideon=0

    def attaquer(self):
        if self.persochoisi:
            qui=self.ciblechoisi[1]
            cible=self.ciblechoisi[2]
            sorte=self.ciblechoisi[5]
            action=[self.parent.parent.monnom,"attaquer",[self.persochoisi,[qui,cible,sorte]]]
            self.parent.parent.actionsrequises.append(action)

    def deplacer(self):
        if self.persochoisi:
            action=[self.parent.parent.monnom,"deplacer",[self.position,self.persochoisi]]
            self.parent.parent.actionsrequises.append(action)

    def chasser_ressource(self,tag):
        if self.persochoisi:
            action=[self.parent.parent.monnom,"chasserressource",[tag[4],tag[2],self.persochoisi]]
            self.parent.parent.actionsrequises.append(action)

    def ramasser_ressource(self,tag):
        if self.persochoisi:
            action=[self.parent.parent.monnom,"ramasserressource",[tag[4],tag[2],self.persochoisi]]
            self.parent.parent.actionsrequises.append(action)

    def construire_batiment(self,pos):
        self.btnactif.config(bg="SystemButtonFace")
        self.btnactif=None
        action=[self.parent.monnom,"construirebatiment",[self.persochoisi,self.prochaineaction,pos]]
        self.parent.parent.actionsrequises.append(action)

    def afficher_commande_perso(self):
        self.widgetsactifs=self.parent.canevasaction.create_window(100,60,
                                                window=self.parent.cadreouvrier,
                                                anchor=N)
        self.parent.root.update()
        fh=self.parent.cadreouvrier.winfo_height()
        ch=int(self.    parent.canevasaction.cget("height"))
        if fh+60>ch:
            cl=int(self.parent.canevasaction.cget("width"))
            self.parent.canevasaction.config(scrollregion=(0,0,cl,fh+60))


    def envoyer_chat(self,evt):
        txt=self.parent.entreechat.get()
        joueur=self.parent.joueurs.get()
        if joueur:
            action=[self.parent.monnom,"chatter",[self.parent.monnom+": "+txt,self.parent.monnom,joueur]]
            self.parent.parent.actionsrequises.append(action)

    def chatter(self):
        if self.chaton==0:
            x1,x2=self.parent.scrollH.get()
            x3=self.parent.modele.aireX*x1
            y1,y2=self.parent.scrollV.get()
            y3=self.parent.modele.aireY*y1
            self.parent.cadrechaton=self.parent.canevas.create_window(x3,y3,
                                                window=self.parent.cadrechat,
                                                anchor=N+W)
            self.parent.btnchat.config(bg="SystemButtonFace")
            self.chaton=1
        else:
            self.parent.canevas.delete(self.parent.cadrechaton)
            self.parent.cadrechaton=0
            self.chaton=0

    def aider(self):
        if self.aideon==0:
            x1,x2=self.parent.scrollH.get()
            x3=self.parent.modele.aireX*x2
            y1,y2=self.parent.scrollV.get()
            y3=self.parent.modele.aireY*y1
            self.aideon=self.parent.canevas.create_window(x3,y3,
                                                window=self.parent.cadreaide,
                                                anchor=N+E)
        else:
            self.parent.canevas.delete(self.aideon)
            self.aideon=0


    ### FIN des methodes pour lancer la partie

class Champ(Label):
    def __init__(self,master,*args, **kwargs):
        Label.__init__(self,master,*args, **kwargs)
        self.config(font=("arial",13,"bold"))
        self.config(bg="goldenrod3")

