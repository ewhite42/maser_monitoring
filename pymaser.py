# This is a program to reduce maser data
# Created by Ellie White
# Thanks to Larry Morgan and Pedro Salas for input

# Imports.
import numpy as np
import os
import pylab as plt
import subprocess
import groundhog as gh
from astropy.io import fits
from datetime import datetime
from scipy.interpolate import interp1d
from operator import itemgetter

class diffSpectra():

    def __init__(self, src_name, xunit='GHz', yunit='Ta*'):
        self.src_name = src_name
        self.xunit = xunit
        self.yunit = yunit

    def correctSpectrum(self, spec, vframe):
        c = 3*(10**8)
        beta = vframe / c
        vframe_corr = np.sqrt((1.0 + beta)/(1.0 - beta))
        return spec*vframe_corr

    def createLaTeX(self, filenames, ts, flags):
        texname = '{}_{}.tex'.format(self.src_name.replace('.', ''), ts)
        outfile = open(texname, 'w')
        outfile.write(r'''\documentclass{article}
\usepackage{graphicx}
\usepackage{xcolor}
\graphicspath{ {./} }

\begin{document}''')
        for i in range(len(filenames)):
            f = filenames[i]
            if i in flags:
                outfile.write(r'''{\setlength{\fboxsep}{1pt}
\setlength{\fboxrule}{10pt}
\color{red}
\fbox{\includegraphics[width=\textwidth]{'''+f+'}}\n')
            else:
                outfile.write(r'\includegraphics[width=\textwidth]{'+f+'}\n')

        outfile.write('\end{document}')
        outfile.close()
        return texname

    def findRecentFiles(self, directory=os.getcwd()):
        # search working directory for files with source_name in their name
        filelist = os.listdir(directory)
        candidate_files = []

        for f in filelist:
            if self.src_name in f:
                candidate_files.append(f)
    
        # convert timestamps in filename into datetime objects
        # determine which two files are most recent
        ts_and_filename = []

        for c in candidate_files:
            # split filename in 2 parts -- source name and timestamp 
            ts_and_ext = c.replace(self.src_name, '').split('.')
            ts_string = ts_and_ext[0]
            extension = ts_and_ext[1]

            if extension == 'fits':
            # convert the timestamp string into a datetime object
                timestamp = datetime.strptime(ts_string, '_%Y_%m_%d_%H-%M-%S')
                ts_and_filename.append([timestamp, c])

        # sort list of files by date
        ts_sorted_list = sorted(ts_and_filename, key=itemgetter(0))

        # only want to select the two most recent spectra: 
        spectra = candidate_files
        spectra = ts_sorted_list[-2:]

        #print(spectra)
        return spectra

    def interpolateSpectrum(self, x1, x2, y2):
        # use x1 as the frequency scale we will plot everything against
        # interpolate the y2 data so it will match with the x1 scale

        f = interp1d(x2, y2, kind='linear')
        y2_new = f(x1)

        return y2_new

    def overlappingIndices(self, freq1, freq2): 
        # this function finds the indices of the section of each 
        # spectrum that overlaps with the other so we can subtract one
        # from the other

        # first, find minimum overlapping frequency
        if freq1[0] < freq2[0]:
            min_freq = freq2[0]
        elif freq2[0] < freq1[0]:
            min_freq = freq1[0]
        elif freq2[0] == freq1[0]:
            min_freq = freq1[0]

        # next, find maximum overlapping frequency
        if freq1[-1] < freq2[-1]:
            max_freq = freq1[-1]
        elif freq2[-1] < freq1[-1]:
            max_freq = freq2[-1]
        elif freq1[-1] == freq2[-1]:
            max_freq = freq1[-1]

        # find intersecting parts of spectra
        idx1 = np.where((freq1>min_freq)*(freq1<max_freq))
        idx2 = np.where((freq2>min_freq)*(freq2<max_freq))

        return idx1, idx2

    def plotAndSave(self, freq, spec, ts, pol, label):

        # creates and saves spectrum plots
        outfilename = '{}_{}_{}pol_{}.png'.format(self.src_name.replace('.',''), ts, pol, label)
        if label == 'diff':
            title = 'Difference between spectra ({}-polarisation)'.format(pol)
        elif label == 'spec1':
            title = '{} spectrum ({}-polarisation) -- {}'.format(self.src_name, pol, ts)
        elif label == 'spec2':
            title = '{} spectrum ({}-polarisation) -- {}'.format(self.src_name, pol, ts)
        else:
            title = 'ERROR -- wrong label specified'
            print(title)
            return 0

        plt.plot(freq, spec)
        plt.title(title)
        plt.xlabel('Freq ({})'.format(self.xunit))
        plt.ylabel('{}'.format(self.yunit))
        plt.savefig(outfilename)
        plt.show()

        return outfilename

    def readFits(self, filename):
        #print(filename)
        sdfits = fits.open(filename)
        table = sdfits[1].data

        #create the frequency array
        bw = table['BANDWID'][0]
        cfreq = table['OBSFREQ'][0]
        freq_res = table['FREQRES'][0]
        channels = int(bw / freq_res)
        freq = np.linspace(cfreq-(0.5*bw), cfreq+(0.5*bw), channels)

        xdata = table['DATA'][0]
        ydata = table['DATA'][1]

        return freq, xdata, ydata, table['VFRAME'][0]

    def run(self):
        fnames_ts = self.findRecentFiles()
    
        freq1, xdata1, ydata1, vframe1 = self.readFits(fnames_ts[0][1])
        freq2, xdata2, ydata2, vframe2 = self.readFits(fnames_ts[1][1])

        ts1 = fnames_ts[0][0].strftime("%Y-%m-%dT%H-%M-%S")
        ts2 = fnames_ts[1][0].strftime("%Y-%m-%dT%H-%M-%S")

        # correct the frequencies for doppler shift 
        freq1_corr = self.correctSpectrum(freq1, vframe1)
        freq2_corr = self.correctSpectrum(freq2, vframe2)

        # find indices of overlapping parts of spectra to subtract
        idx1, idx2 = self.overlappingIndices(freq1_corr, freq2_corr)

        freq1_corr_sliced = freq1_corr[idx1]
        freq2_corr_sliced = freq2_corr[idx2]

        xdata1_sliced = xdata1[idx1]
        ydata1_sliced = ydata1[idx1]
        xdata2_sliced = xdata2[idx2]
        ydata2_sliced = ydata2[idx2] 
   
        xdata2_new = self.interpolateSpectrum(freq1_corr_sliced, freq2_corr_sliced, xdata2_sliced)
        ydata2_new = self.interpolateSpectrum(freq1_corr_sliced, freq2_corr_sliced, ydata2_sliced)

        # select just the region of the spectra around the maser line
        nchan = len(xdata1_sliced)

        xdata1_sliced = xdata1_sliced[int(nchan*0.05):int(nchan*0.95)]
        ydata1_sliced = ydata1_sliced[int(nchan*0.05):int(nchan*0.95)]
        xdata2_new = xdata2_new[int(nchan*0.05):int(nchan*0.95)]
        ydata2_new = ydata2_new[int(nchan*0.05):int(nchan*0.95)]

        freq1_corr_sliced = freq1_corr_sliced[int(nchan*0.05):int(nchan*0.95)]

        # find average of the x and y polarisation spectra
        avgdata2_new = (xdata2_new + ydata2_new)/2
        avgdata1_sliced = (xdata1_sliced + ydata1_sliced)/2

        # difference the spectra
        spec_diff_x = xdata2_new - xdata1_sliced
        spec_diff_y = ydata2_new - ydata1_sliced
        spec_diff_avg = avgdata2_new - avgdata1_sliced

        current_ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

        if self.xunit == 'GHz':
            freq1_corr_sliced = freq1_corr_sliced / (10**9)

        # create pngs and collect the corresponding filenames
        png_fnames = []

        # plot x spectra
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, xdata1_sliced, ts1, 'x', 'spec1'))
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, xdata2_new, ts2, 'x', 'spec2'))        
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, spec_diff_x, current_ts, 'x', 'diff'))

        # plot y spectra
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, ydata1_sliced, ts1, 'y', 'spec1'))
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, ydata2_new, ts2, 'y', 'spec2'))
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, spec_diff_y, current_ts, 'y', 'diff'))

        # plot spectral differences
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, avgdata1_sliced, ts1, 'avg', 'spec1'))
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, avgdata2_new, ts2, 'avg', 'spec2')) 
        png_fnames.append(self.plotAndSave(freq1_corr_sliced, spec_diff_avg, current_ts, 'avg', 'diff'))

        # threshold check
        flags = []

        '''if not self.thresholdCheck(spec_diff_x):
            flags.append(2)
        if not self.thresholdCheck(spec_diff_y):
            flags.append(5)
        if not self.thresholdCheck(spec_diff_avg):
            flags.append(8)'''

        flags = [3, 8]

        # create latex file to generate pdf from
        tex_fname = self.createLaTeX(png_fnames, current_ts, flags)

        # run pdflatex to create the pdf
        subprocess.run(['pdflatex', tex_fname])

    def setSourceName(self, src_name):
        self.src_name = src_name
        return self.src_name

    def thresholdCheck(self, data):
        threshold = 3*np.std(data)
        data_lst = data.tolist()
        for d in data_lst:
            if float(d) > threshold:
                print('Threshold exceeded!')
                return 0
        return 1

def main():

    # src_list = sources from catalog
    # ds = diffSpectra(src_list[0])
    # ds.run()

    # for s in src_list[1:]:
    #     ds.setSourceName(s)
    #     ds.run()

    ds = diffSpectra('G013.179+0.061')
    ds.run()

if __name__ == '__main__':
    main()
