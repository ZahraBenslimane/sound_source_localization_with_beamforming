import numpy as np
import numpy.matlib as npm
import scipy.special as scsp
import matplotlib.pyplot as plt

import IPython
from matplotlib import cm

import os
import time

working_dir = os.getcwd()

# Physical parameters
c0 = 343
rho0 = 1.2
dyndB = 10
# Topographic parameters
Lx = 50
Ly = 75
Lz = 35

# Array configuration
NbMics = 32
## Single ring
Nrings  = 1
Rring   = 0.5
Nmring  = NbMics//Nrings
THmring = np.linspace(0,2*np.pi,Nmring)
Xmring  = np.cos(THmring) *Rring
Ymring =  np.sin(THmring) *Rring
Zmring =  np.zeros_like(Xmring)

Rr0 = np.array([0,0, Lz])  
Rm = np.array([Xmring, Ymring, Zmring]) + Rr0[:,np.newaxis]
[Xm, Ym, Zm] = Rm

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm

color = ['b','g','r','c','m','y','k' ]

fig = plt.figure(figsize = (5,5), clear = True)
ax = fig.add_subplot(111, projection ='3d')
ax.scatter(Xm, Ym, Zm)
ax.set_xlim(-Lx/2, Lx/2)
ax.set_ylim(-Ly/2, Ly/2)
ax.set_zlim(0, Lx/2)
#%%
#Simulation de la scène directe

#Scénario 7 sources disposées aléatoirement dans l'espace et dans le temps
# première partie  : chaque source seule
# deuxième partie  : 2 sources en même temps (différentes combinaisons)
# troisième partie : toutes les sources en même temps

xo = np.random.rand(7)*Lx-Lx/2
yo = np.random.rand(7)*Ly-Ly/2
zo = np.zeros_like(xo)
Ro = np.vstack((xo,yo,zo))

ax.scatter(xo, yo, zo, c = color, s=500)

# Signal sur les micros
Rom = np.linalg.norm(Rm[:,np.newaxis,:]-Ro[:,:,np.newaxis], axis = 0)

TestFiles = os.listdir('./test')

from scipy.io import wavfile
#Fichiers son déphasés suivant l'agencement des micros et des sources
Fe = 50000
T = 5
N = T*Fe
Sigsm = np.random.randn(7,N,32)*5e7*0
for f in TestFiles:
    if f.startswith('Cls'):
        Fe, Snd = wavfile.read('./test/'+f)
        Cls = int(f[4])-1
        print(Cls, N)
        Spec = np.fft.rfft(Snd, N)
        freq = np.fft.rfftfreq(N, 1/Fe)
        g = np.exp(-2*1j*np.pi*freq[:, np.newaxis]*Rom[Cls,:]/c0)/Rom[Cls,:]
        Specsm = Spec[:,np.newaxis]*g
        Sigsm[Cls,:,:] += np.fft.irfft(Specsm, axis = 0)
        Sigsm[1,:,:]*=3

Sigs = np.zeros((32,1))        
Scenario={'T': T}
ii = 0
## Partie 1
for Cls in range(7) : 
     Sigs = np.hstack((Sigs,Sigsm[Cls,:,:].T))
     Scenario['S' + str(ii)]=[Cls]
     ii += 1
## Partie 2     
for Cls1 in range(7):    
    for Cls2 in range(Cls1+1, 7):       
        Sigs = np.hstack((Sigs,Sigsm[Cls1,:,:].T+Sigsm[Cls2,:,:].T))
        Scenario['S' + str(ii)] = [Cls1, Cls2] 
        ii += 1
## Partie 3        
Sigs = np.hstack((Sigs,np.sum(Sigsm,axis = 0).T))
Scenario['S' + str(ii)] = np.arange(7) 
print(Scenario)
#%%
np.savez('SimulatedData.npz', Sigs=Sigs, SrcPos = Ro, MicsPos = Rm, Lx = Lx, Ly = Ly, scenario = Scenario, T = T)
import scipy.io as io
dico = {'Sigs':Sigs}
io.savemat('Sigs.mat', dico)