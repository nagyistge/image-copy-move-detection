__author__ = 'rahmat'
# 14 November 2016 5:28 PM

"""
Import library
"""
from PIL import Image
import scipy.misc
from math import pow
import numpy as np
import __builtin__
import sys
import time

"""
Import script
"""
import Container
import Blocks

class ImageObject(object):
    """
    Objek untuk menampung sebuah citra dan melakukan deteksi pemalsuan pada citra tersebut
    """

    def __init__(self, imageDir, imageName, blockDimension, targetResult):
        """
        Fungsi konstruktor untuk mempersiapkan citra dan parameter algoritma
        :param imageDir: direktori file citra
        :param imageName: nama file citra
        :param blockDimension: ukuran blok dimensi (ex:32, 64, 128)
        :param targetResult: direktori untuk hasil deteksi
        :return: None
        """

        print imageName
        print "Step 1: Inisialisasi objek dan variable",

        # parameter gambar
        self.targetResult = targetResult
        self.imagePath = imageName
        self.image = Image.open(imageDir+imageName)
        self.imageWidth, self.imageHeight = self.image.size      # height = vertikal atas bawah, width = horizontal lebar kanan kiri

        # parameter algoritma paper 1
        self.N = self.imageWidth * self.imageHeight
        self.blockDimension = blockDimension
        self.b = self.blockDimension * self.blockDimension
        self.Nb = (self.imageWidth-self.blockDimension+1)*(self.imageHeight-self.blockDimension+1)
        self.Nn = 2      # jumlah blok tetangga yang diperiksa
        self.Nf = 750    # jumlah minimal frekuensi sebuah offset
        self.Nd = 50     # jumlah minimal offset magnitude

        # parameter algoritma paper 2
        self.P = (1.80, 1.80, 1.80, 0.0125, 0.0125, 0.0125, 0.0125)
        self.t1 = 2.80
        self.t2 = 0.02

        print "total blok: ", self.Nb

        # inisialisasi kontainer untuk menampung data
        self.featureContainer = Container.Container()
        self.pairContainer = Container.Container()
        self.offsetDict = {}

    def run(self):
        """
        Fungsi untuk menjalankan serangkaian langkah algoritma
        :return: None
        """

        start = time.time()
        self.compute()
        end1 = time.time()
        self.sort()
        end2 = time.time()
        self.analyze()
        end3 = time.time()
        self.reconstruct()
        end4 = time.time()

        print "Computing time:", end1-start, "detik"
        print "Sorting time  :", end2-end1, "detik"
        print "Analyzing time:", end3-end2, "detik"
        print "Image creation:", end4-end3, "detik"

        totalSecond = end4-start
        m, s = divmod(totalSecond, 60)
        h, m = divmod(m, 60)
        print "Total time    : %d:%02d:%02d detik" % (h, m, s)
        print ""

    def compute(self):
        """
        Fungsi untuk menghitung karakteristik blok citra
        :return: None
        """
        print "Step 2: Menghitung fitur karakteristik dan PCA"
        z = 0
        for i in range(0, self.imageWidth - self.blockDimension + 1):
            for j in range(0, self.imageHeight - self.blockDimension + 1):
                tmpImage = self.image.crop((i, j, i+self.blockDimension, j+self.blockDimension))
                imageBlock = Blocks.Blocks(tmpImage, i, j, self.blockDimension)
                self.featureContainer.addBlock(imageBlock.computeBlock())
                del tmpImage, imageBlock
                z+=1
                if z % 100 == 0:
                    sys.stdout.write("    terhitung: %3d blok\r" % z)
                    sys.stdout.flush()

            #     if z == 2000:
            #         break
            # if z == 2000:
            #     break
        print "    total blok citra:", z

    def sort(self):
        """
        Memanggil fungsi sort pada objek Container
        :return: None
        """
        self.featureContainer.sortFeatures()

    def analyze(self):
        """
        Fungsi untuk melakukan analisa pasangan blok citra
        :return: None
        """
        print "Step 3: Membuat block pair yang berjarak < Nn"
        z = 0
        for i in range(0, self.featureContainer.getLength()):
            for j in range(i+1, self.featureContainer.getLength()):
                result = self.isValid(i, j)
                if result[0]:
                    self.addDict(self.featureContainer.container[i][0], self.featureContainer.container[j][0], result[1])
                    z += 1
                else:
                    break

                if z % 100 == 0 or i % 100 == 0:
                    sys.stdout.write("    hasil sementara: %3d blok terperiksa, %3d pasang didapat\r" % (i, z))
                    sys.stdout.flush()
        print "    pasangan data yang didapatkan:", z

    def isValid(self, i, j):
        """
        Fungsi untuk mengecek validitas pasangan blok; mencari offset, menghitung magnitude, absolut i dan j,
        serta validitas blok dari fitur karakteristik
        :param i: blok 1
        :param j: blok 2
        :return: apakah pasangan i,j valid ?
        """

        if abs(i-j) < self.Nn:
            iFeature = self.featureContainer.container[i][1]
            jFeature = self.featureContainer.container[j][1]

            # cek validitas nilai karakteristik fitur dari paper 2
            if abs(iFeature[0] - jFeature[0]) < self.P[0]:
                if abs(iFeature[1] - jFeature[1]) < self.P[1]:
                    if abs(iFeature[2] - jFeature[2]) < self.P[2]:
                        if abs(iFeature[3] - jFeature[3]) < self.P[3]:
                            if abs(iFeature[4] - jFeature[4]) < self.P[4]:
                                if abs(iFeature[5] - jFeature[5]) < self.P[5]:
                                    if abs(iFeature[6] - jFeature[6]) < self.P[6]:
                                        if abs(iFeature[0] - jFeature[0]) + abs(iFeature[1] - jFeature[1]) + abs(iFeature[2] - jFeature[2]) < self.t1:
                                            if abs(iFeature[3] - jFeature[3]) + abs(iFeature[4] - jFeature[4]) + abs(iFeature[5] - jFeature[5]) + abs(iFeature[6] - jFeature[6]) < self.t2:

                                                # mencari offset dari masing-masing pasangan
                                                iCoordinate = self.featureContainer.container[i][0]
                                                jCoordinate = self.featureContainer.container[j][0]

                                                # Robust Detection Non Absolute
                                                offset = (iCoordinate[0] - jCoordinate[0], iCoordinate[1] - jCoordinate[1])

                                                # menghitung magnitude
                                                magnitude = np.sqrt(pow(offset[0], 2) + pow(offset[1], 2))
                                                if magnitude >= self.Nd:
                                                    return 1, offset
        return 0,

    def addDict(self, coor1, coor2, offset):
        """
        Fungsi untuk menambahkan pasangan coor1, coor2, dan offsetnya kedalam dictionary
        """
        if self.offsetDict.has_key(offset):
            self.offsetDict[offset].append(coor1)
            self.offsetDict[offset].append(coor2)
        else:
            self.offsetDict[offset] = [coor1, coor2]

    def reconstruct(self):
        """
        Fungsi untuk melakukan konstruksi ulang citra dengan menyertakan hasil dugaan deteksi
        """
        print "Step 10: Reconstructing Image"

        # array pembentuk citra hasil
        imageArray = np.zeros((self.imageHeight, self.imageWidth))
        scale = np.array(self.image)
        lined = np.array(self.image)

        for key in sorted(self.offsetDict, key=lambda key: __builtin__.len(self.offsetDict[key]), reverse=True):
            if self.offsetDict[key].__len__() < self.Nf*2:
                break
            print key, self.offsetDict[key].__len__()
            for i in range(self.offsetDict[key].__len__()):
                # gambar hasil (hitam putih)
                for j in range(self.offsetDict[key][i][1], self.offsetDict[key][i][1]+self.blockDimension):
                    for k in range(self.offsetDict[key][i][0], self.offsetDict[key][i][0]+self.blockDimension):
                        imageArray[j][k] = 255

        # color scale gambar asli
        for y in range(0, self.imageWidth):
            for x in range(0, self.imageHeight):
                if imageArray[x,y] == 255:
                    scale[x,y,2] = 255

        # lined gambar asli
        for x in range(2, self.imageHeight-2):
            for y in range(2, self.imageWidth-2):
                if imageArray[x,y] == 255 and (imageArray[x+1,y] == 0 or imageArray[x-1,y] == 0 or
                                                        imageArray[x,y+1] == 0 or imageArray[x,y-1] == 0 or
                                                        imageArray[x-1,y+1] == 0 or imageArray[x+1,y+1] == 0 or
                                                        imageArray[x-1,y-1] == 0 or imageArray[x+1,y-1] == 0):

                    # ujung kiri atas, kanan atas, kiri bawah, kanan bawah
                    if imageArray[x-1,y] == 0 and imageArray[x,y-1] == 0 and imageArray[x-1,y-1] == 0:
                        lined[x-2:x,y,1] = 255
                        lined[x,y-2:y,1] = 255
                        lined[x-2:x,y-2:y,1] = 255
                    elif imageArray[x+1,y] == 0 and imageArray[x,y-1] == 0 and imageArray[x+1,y-1] == 0:
                        lined[x+1:x+3,y,1] = 255
                        lined[x,y-2:y,1] = 255
                        lined[x+1:x+3,y-2:y,1] = 255
                    elif imageArray[x-1,y] == 0 and imageArray[x,y+1] == 0 and imageArray[x-1,y+1] == 0:
                        lined[x-2:x,y,1] = 255
                        lined[x,y+1:y+3,1] = 255
                        lined[x-2:x,y+1:y+3,1] = 255
                    elif imageArray[x+1,y] == 0 and imageArray[x,y+1] == 0 and imageArray[x+1,y+1] == 0:
                        lined[x+1:x+3,y,1] = 255
                        lined[x,y+1:y+3,1] = 255
                        lined[x+1:x+3,y+1:y+3,1] = 255
                    # atas bawah kiri kanan
                    elif imageArray[x,y+1] == 0:
                        lined[x,y+1:y+3,1] = 255
                    elif imageArray[x,y-1] == 0:
                        lined[x,y-2:y,1] = 255
                    elif imageArray[x-1,y] == 0:
                        lined[x-2:x,y,1] = 255
                    elif imageArray[x+1,y] == 0:
                        lined[x+1:x+3,y,1] = 255

        timestr = time.strftime("%Y%m%d_%H%M%S_")
        scipy.misc.imsave(self.targetResult+timestr+self.imagePath, imageArray)
        scipy.misc.imsave(self.targetResult+timestr+"_scale_"+self.imagePath, scale)
        scipy.misc.imsave(self.targetResult+timestr+"_lined_"+self.imagePath, lined)
