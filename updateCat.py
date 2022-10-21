def initCat():

    fname = 'MMBGroup1.cat'
    ofname = 'MMBGroup1_rev.cat'

    infile = open(fname, 'r')
    filetext = infile.readlines()
    filetext[3] = filetext[3][:-1]+'\t     TIMESTAMP\n'
    newlines = []

    for line in filetext[4:]:
        newlines.append(line[:-1]+'\t0')

    outfile = open(ofname, 'w')
    outfile.write(''.join(filetext[0:4])+'\n'.join(newlines))
    outfile.close()
    infile.close()

def updateCat(fname, ofname, src_name, timestamp):
    infile = open(fname, 'r')
    filetext = infile.readlines()   
    newlines = []

    for line in filetext[4:]:
        fields = line.split()
        if fields[0] == src_name:
            fields[5] = timestamp
            newlines.append('   '.join(fields)+'\n')
        else:
            newlines.append(line) 

    infile.close()
    outfile = open(ofname, 'w')
    outfile.write(''.join(filetext[0:4])+''.join(newlines))
    outfile.close()


if __name__ == '__main__':
    #initCat()

    updateCat('MMBGroup1_rev.cat', 'MMBGroup1_updated.cat', 'G033.486+0.040', '14:20')
