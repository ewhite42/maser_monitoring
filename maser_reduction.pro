; This program is intended to automatically reduce maser data
; use TGBT22A_502_00 as example data
pro maser_reduction

ProjFile = '/home/scratch/lmorgan/AGBT20A_250/Data/AGBT20A_250_01.raw.vegas/AGBT20A_250_01.raw.vegas.B.fits' ;'TGBT22A_502_00'
SumFile=strcompress(ProjFile+'_Summary.txt',/remove_all)
xpol = 2
ypol = 3

filein, ProjFile

; Read the summary file
if not (file_test(SumFile)) then begin
  summary,SumFile
  print,'Summary file not found, creating it'
endif

readcol,SumFile, $
Scan,Source,Vel,Proc,Seq,RestF,nIF,nInt,nFd,Az,El, $
format='I,A,F,A,I,F,I,I,I,F,F',skipline=2,/silent

;create the reduced spectra
for i=0, N_ELEMENTS(Scan)-1 do begin &$
    if ((Proc[i] EQ 'OffOn') OR (Proc[i] EQ 'OnOff')) AND (Seq[i] EQ 1) then begin
        getps, Scan[i], plnum=xpol, units='Ta*'
        ts = repstr(STRING(!g.s[0].timestamp), ':', '-')
        
        ;find number of channels
        a = getdata()
        nchan = n_elements(a)

        ;subtract the baseline
        nregion, [round(nchan*0.05), round(nchan*0.45), round(nchan*0.55), round(nchan*0.95)]
        nfit, 3
        baseline
        fileout, Source[i]+'_'+ts+'.fits'
        keep

        getps, Scan[i], plnum=ypol, units='Ta*'
        nregion, [round(nchan*0.05), round(nchan*0.45), round(nchan*0.55), round(nchan*0.95)]
        nfit, 3
        baseline
        keep
    endif

    if (Proc[i] EQ 'Track') AND (Seq[i] EQ 1) then begin
        getfs, Scan[i], plnum=xpol, units='Ta*'
        ts = repstr(STRING(!g.s[0].timestamp), ':', '-')
        
        ;find number of channels
        a = getdata()
        nchan = n_elements(a)

        ;subtract the baseline
        nregion, [round(nchan*0.05), round(nchan*0.45), round(nchan*0.55), round(nchan*0.95)]
        nfit, 3
        baseline
        fileout, Source[i]+'_'+ts+'.fits'
        keep

        getfs, Scan[i], plnum=ypol, units='Ta*'
        nregion, [round(nchan*0.05), round(nchan*0.45), round(nchan*0.55), round(nchan*0.95)]
        nfit, 3
        baseline
        keep
    endif
    
end

end
