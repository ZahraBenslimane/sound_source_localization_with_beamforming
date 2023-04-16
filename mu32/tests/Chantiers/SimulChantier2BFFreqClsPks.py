# -*- coding: utf-8 -*-
# import required libraries
#%%###########################################################################
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sig
import os
import matplotlib.dates as dates
import datetime
import wave
import struct
from findpeaks import findpeaks
import matplotlib.animation as manimation

#%%###########################################################################
# import speech features and IA libraries
import python_speech_features as sp
import tensorflow as tf
#from tensorflow import set_random_seed
#from numpy.random import seed
os.environ['KMP_DUPLICATE_LIB_OK']='True'

#%%###########################################################################
#Sensibilité : -26dBFS pour 104 dB soit 3.17 Pa
FS = 2**23
S = FS*10**(-26/20.) / 3.17
po = 20e-6
Fs = 50000
NumMicPlot = 1
plt.close('all')
datadir = './'

#%%###########################################################################
# set speech features and IA parameters
filt_n = 26
lowfreq = 0
highfreq = None
preemph = 0.97
ceplifter = 22
appendEnergy = True
mffc_dim=16
win_len=0.100
win_step=0.050
fft_n = int( win_len*Fs )
energy_threshold = 0.01

#%%###########################################################################
## Init neural network 
##################################################################
N_SAMPLES = 1
BATCH_SIZE = N_SAMPLES
INPUT_LENGTH = 16
INPUTS_SHAPE = (BATCH_SIZE, INPUT_LENGTH)
N_CLASSES = 7
N_HLAYER1 = 120
N_HLAYER2 = 84
mm_model = tf.keras.models.Sequential()
mm_model.add(tf.keras.layers.Dense(N_HLAYER1 , activation='tanh', input_shape=(INPUT_LENGTH,)))
mm_model.add(tf.keras.layers.Dense(N_HLAYER2 , activation='tanh'))
mm_model.add(tf.keras.layers.Dense(N_CLASSES , activation='softmax'))
print(mm_model.summary())
sgd = tf.keras.optimizers.SGD(lr=0.01, momentum=0.9, nesterov=True)
mm_model.compile(sgd, loss='categorical_crossentropy', metrics=['accuracy'])
# load weights:
mm_model.load_weights('./Networkweights.h5', by_name=False)

# Physical parameters
c0 = 343
rho0 = 1.2
dyndB = 10
# Topographic parameters
d = 2.5
dfen = 10

Data = np.load('SimulatedData.npz')
Rm = np.load('SimulatedData.npz')['MicsPos']
Ro = np.load('SimulatedData.npz')['SrcPos']
Sigs = np.load('SimulatedData.npz')['Sigs']
Lx = np.load('SimulatedData.npz')['Lx']
Ly = np.load('SimulatedData.npz')['Ly']
T = np.load('SimulatedData.npz')['T'] 
Scenar = np.load('SimulatedData.npz', allow_pickle = True)['scenario'].tolist()

NbMics = Rm.shape[1]
#%%
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
color = ['b','g','r','c','m','y','k' ]
# fig = plt.figure(figsize = (5,5), clear = True)
# ax = fig.add_subplot(111, projection ='3d')
# ax.scatter(*Rm)
# ax.scatter(*Ro, c = color, s=50)
# ax.set_xlim(-Lx/2, Lx/2)
# ax.set_ylim(-Ly/2, Ly/2)
# ax.set_zlim(0, Lx/2)
#%%##################################################################
print('Initialisation BeamForming')
#StdBF###########################################################################

xs = np.arange(-Lx/2,Lx/2,d),
ys = np.arange(-Ly/2, Ly/2, d)
nx,ny = int(Lx/d), int(Ly/d)
npix = nx*ny
[Xs, Ys] = np.meshgrid(xs,ys)
Xs = Xs.flatten()
Ys = Ys.flatten()
Zs = np.zeros_like(Xs)
Rs = np.array([Xs, Ys, Zs])
Rms = np.linalg.norm(Rs[:,np.newaxis,:]-Rm[:,:,np.newaxis], axis = 0)

f = np.fft.rfftfreq(int(Fs/dfen), 1/Fs)

G = np.outer(f,Rms).reshape(f.shape[0],Rms.shape[0], Rms.shape[1])/c0
G = np.exp(1j*2*np.pi*G)

#%%###################################################################
## Affichage 
##################################################################/home/francois/Data/Labo/Projets/Beameo/Dvpt/SimulChantier
#intialisation des graphiques

plt.ion()
fig = plt.figure(1, clear = True, figsize=(10, 10))


#%%###################################################################
## Traitement données 
##################################################################

##################################################################
## Traitement des sequences et affichage du BF
##################################################################
Debut = 0
Duree = Sigs.shape[1]/Fs
Fin  = Debut+Duree
dfen = 10
energy_threshold = 0.1
NbCls = 7
ChrCls = -np.ones((2*NbCls, int(Duree*dfen)))
BFMap = np.zeros((nx, ny))
ClsMap = np.empty((nx, ny))
#%%####### ChronoCartographie 1

cmap = plt.cm.get_cmap('Accent', NbCls)
cmap.set_under('k')

ax_ChrCls = fig.add_subplot(121)
ax_ChrCls.set_xlabel('pixel')
ax_ChrCls.set_ylabel('time')
ChrClsMap = ax_ChrCls.imshow(ChrCls, extent = [-0.5, NbCls-0.5, 0, Duree*dfen],  interpolation='nearest',
                              vmin = -0.5, vmax = NbCls-0.5, cmap = cmap, aspect = 'auto', origin ='lower')

fig.colorbar(ChrClsMap, ax = ax_ChrCls, ticks=range(NbCls))

ax_BF = fig.add_subplot(222)
ax_BF.set_xlabel('X (m)')
ax_BF.set_ylabel('Y (m)')
BFCarte = ax_BF.imshow(BFMap, extent = [-Lx/2, Lx/2, -Ly/2, Ly/2], interpolation='nearest', 
                              vmin = 0.5, vmax = 1, cmap = 'inferno', aspect = 'equal', origin ='lower')
color = cmap(range(7))
ax_BF.scatter(Ro[0], Ro[1], c =color , s = 100)

ax_Cls = fig.add_subplot(224)
ax_Cls.set_xlabel('X (m)')
ax_Cls.set_ylabel('Y (m)')
ClsCarte = ax_Cls.imshow(ClsMap, extent = [-Lx/2, Lx/2, -Ly/2, Ly/2],  interpolation='nearest',
                              vmin = 0, vmax = NbCls-1, cmap = cmap, aspect = 'equal', origin ='lower')
ax_Cls.scatter(Ro[0], Ro[1], c =color , s=100)

#fig.colorbar(BFMap, ax = ax_BF, ticks=range(NbCls+1))
ax_ChrCls.set_title('')
plt.tight_layout(pad = 2)

print( 'Process sequences...' )
print( 'Opening file FiltreFV.wav, channels: ' + str(nx*ny) + ', samplewidth: 4, framerate: ' + str(Fs) )
cl = open( datadir+'/Class.csv', 'w' )
cl.write( 'Séquence;Trame;Classe;Accuracy;Energie;Energie moyenne' )

NbSeqs = int(Sigs.shape[1]/Fs)
NumSec = 0
detect_n = 0

jj = 0

for i in range(NbSeqs//T):
    Sce = Scenar['S' + str(i)]
    T = Scenar['T']
    for Cls in Sce : 
        ChrCls[2*Cls, i*T*10:(i+1)*T*10] = Cls
ChrClsMap.set_array(ChrCls.T)
fig.canvas.draw()
fig.canvas.flush_events() 
plt.draw()
plt.show()
# Initialize
fp = findpeaks(method='mask')
fp = findpeaks(scale=True, denoise='fastnl', window=3, togray=True, imsize=(nx,ny))
#NbSeqs = 2

exit()

for NumSec in range(NbSeqs):
    # Pour chaque séquence d'une seconde:       
    print( 'processing sequence  - ' + str(int(NumSec)) + '/' + str(NbSeqs))
    Sec = Sigs[:, NumSec*Fs:(NumSec+1)*Fs].T/S/100
    Text = 'Scenar'
    
    for ii in range(10):
        # pour chaque trame de 100ms:
        Spec = np.fft.rfft(Sec[ii*int(Fs/dfen) + np.arange(int(Fs/dfen)),:], axis=0)
        SpecG = Spec[:, :, None]*G
        BFSpec = np.sum(SpecG,1)/NbMics
        BFSig = np.fft.irfft(BFSpec, axis = 0)
        BF = np.mean(np.abs(BFSig)**2,0)
        # Détection des pics sur toutes les voies:                
        iBFmax = np.argmax(BF)
        # Fit        
        fp.fit(BF.reshape((ny,nx)))
        iPics = np.argwhere(fp.results['Xdetect'].flatten())         
        carte = -np.ones_like(BF)
        for iPic in iPics : 
            # Détection -> classification de la trame:
            if BF[iPic]>energy_threshold:
                detect_n = detect_n + 1
                # calcul des mfcc sur la voie:
                frame_mfcc =  sp.mfcc(BFSig[:,iPic], Fs, win_len, win_step, mffc_dim, 
                                      filt_n, fft_n, lowfreq, highfreq, preemph, ceplifter, appendEnergy )
                #prédiction :
                frame_pred = mm_model.predict(frame_mfcc)
                frame_pred = frame_pred[0,:]
                # classement de la trame:
                frame_label = np.argmax(frame_pred)+1
                # affichage et envoi:
                Accuracy = round(frame_pred[frame_label-1],2)
                if Accuracy >= 0.85:
                    lbl = frame_label -1
                    ChrCls[2*lbl+1,jj] = lbl         
                else:
                    lbl= -1
                
                carte[iPic] = lbl
                print(lbl)
        jj += 1
            
        ChrClsMap.set_array(ChrCls.T)
        ax_ChrCls.set_title(Text)
        BFCarte.set_array(BF.reshape(ny,nx)/np.max(BF))
        ClsCarte.set_array(carte.reshape(ny,nx))
    
        fig.canvas.draw()
        fig.canvas.flush_events() 
        plt.draw()
        plt.show()
          
        
cl.close()
print(str(detect_n) + ' détections opérées')

