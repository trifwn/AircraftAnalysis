import os
import numpy as np
from time import sleep
import shutil


def anglesSep(anglesALL):
    pangles = []
    nangles = []
    for ang in anglesALL:
        if ang > 0:
            pangles.append(ang)
        elif ang == 0:
            pangles.append(ang)
            nangles.append(ang)
        else:
            nangles.append(ang)
    nangles = nangles[::-1]
    return nangles, pangles


def makeCLCD(Reynolds, Mach):
    folders = next(os.walk('.'))[1]
    print('OK')
    with open('output_bat', 'w') as file:
        folder = folders[0]
        file.writelines('cd '+folder+'\n../write_out\n')
        for folder in folders[1:]:
            if 'AERLOAD.OUT' in next(os.walk(folder))[2]:
                file.writelines('cd ../'+folder+'\n../write_out\n')

        # Write Cat command
        file.writelines('cd ..\n')
        file.writelines('echo "Reynolds: '+str(Reynolds) +
                        '\\nMach: ' + str(Mach) + '" > clcd.out\n')
        file.writelines('cat ')
        for folder in folders[::-1]:
            if 'AERLOAD.OUT' in next(os.walk(folder))[2]:
                file.writelines(folder+'/clcd.out ')
        file.writelines('>> clcd.out')
    os.system('./output_bat')

    with open('clcd.out', 'r') as file:
        data = file.readlines()
    data = data[2:]
    nums = []
    for item in data:
        n = item.split()
        nums.append([float(i) for i in n])
    clcd = np.array(nums)
    return clcd


def runFw2(Reynolds, Mach, ftripL, ftripU, anglesALL, airfile):
    nangles, pangles = anglesSep(anglesALL)
    for angles, name in [[pangles, 'pos'], [nangles, 'neg']]:
        NoA = len(angles)

        # IO FILES
        fname = 'io.files'
        with open(fname, 'r') as file:
            data = file.readlines()
        data[1] = 'design.inp\n'
        data[2] = 'f2w.inp\n'
        data[3] = airfile + '\n'
        with open(fname, 'w') as file:
            file.writelines(data)

        # DESIGN.INP
        fname = 'design_' + name+'.inp'
        with open(fname, 'r') as file:
            data = file.readlines()
        data[2] = str(NoA) + '           ! No of ANGLES\n'
        data = data[:3]
        for ang in angles:
            data.append(str(ang) + '\n')
        data.append('ANGLE DIRECTORIES (8 CHAR MAX!!!)\n')
        for ang in angles:
            if name == 'pos':
                data.append(str(ang)[::-1].zfill(7)[::-1] + '/\n')
            else:
                data.append(
                    'm'+str(ang)[::-1].strip('-').zfill(6)[::-1] + '/\n')
        with open(fname, 'w') as file:
            file.writelines(data)

        # F2W.INP
        fname = 'f2w_' + name+'.inp'
        with open(fname, 'r') as file:
            data = file.readlines()
        data[30] = np.format_float_scientific(
            Reynolds, sign=False, precision=2).zfill(8) + '  ! Reynolds\n'
        data[32] = str(Mach)[::-1].zfill(3)[::-1] + '      ! Mach     Number\n'
        data[34] = str(ftripL[name])[::-1].zfill(3)[::-1] + \
            '    1  ! TRANSLO\n'
        data[35] = str(ftripU[name])[::-1].zfill(3)[::-1] + \
            '    2  ! TRANSLO\n'
        with open(fname, 'w') as file:
            file.writelines(data)

        # RUN Files
        os.system('cp design_'+name+'.inp design.inp')
        os.system('cp f2w_'+name+'.inp f2w.inp')
        print(f'Running {angles}')
        os.system('./foil > '+name+'.out')
        os.system('rm -r TMP.dir/')
    os.system('rm -r SOLOUTI*')
    sleep(1)
    # return makeCLCD(Reynolds,Mach)
    return 0


def removeResults(angles):
    os.system('rm  SOLOUTI*')
    os.system('rm  *.out')
    os.system('rm PAKETO')
    parentDir = os.getcwd()
    folders = next(os.walk("."))[1]
    for angle in angles:
        if angle >= 0:
            folder = str(angle)[::-1].zfill(7)[::-1] + "/"
        else:
            folder = "m" + str(angle)[::-1].strip("-").zfill(6)[::-1] + "/"
        if folder[:-1] in folders:
            os.chdir(folder)
            os.system(
                'rm -f AERLOAD.OUT AIRFOIL.OUT BDLAYER.OUT COEFPRE.OUT SEPWAKE.OUT TREWAKE.OUT clcd.out SOLOUTI.INI')
            os.chdir(parentDir)


def setupF2W():
    filesNeeded = ['design.inp', 'design_neg.inp', 'design_pos.inp',
                   'f2w.inp', 'f2w_neg.inp', 'f2w_pos.inp', 'io.files', 'write_out']
    for item in filesNeeded:
        shutil.copy(f'../Base/{item}', '.')
    if 'foil' not in next(os.walk('.'))[2]:
        os.system('ln -sv ../../foil foil')
