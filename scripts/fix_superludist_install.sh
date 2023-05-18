#!/usr/bin/env bash

sed -i '$ s/$/\/home\/jsb\/.local\/lib\/libmetis.a \/home\/jsb\/.local\/lib\/libGKlib.a \/home\/jsb\/.local\/lib\/libparmetis.a -lblas/' /home/jsb/PyBaMM/install_KLU_Sundials/build_sundials/examples/arkode/CXX_superludist/CMakeFiles/ark_brusselator1D_FEM_sludist.dir/link.txt

sed -i '$ s/$/\/home\/jsb\/.local\/lib\/libmetis.a \/home\/jsb\/.local\/lib\/libGKlib.a \/home\/jsb\/.local\/lib\/libparmetis.a -lblas/' /home/jsb/PyBaMM/install_KLU_Sundials/build_sundials/examples/cvode/superludist/CMakeFiles/cvAdvDiff_sludist.dir/link.txt

sed -i '$ s/$/\/home\/jsb\/.local\/lib\/libmetis.a \/home\/jsb\/.local\/lib\/libGKlib.a \/home\/jsb\/.local\/lib\/libparmetis.a -lblas/' /home/jsb/PyBaMM/install_KLU_Sundials/build_sundials/examples/sunmatrix/slunrloc/CMakeFiles/test_sunmatrix_slunrloc.dir/link.txt

sed -i '$ s/$/\/home\/jsb\/.local\/lib\/libmetis.a \/home\/jsb\/.local\/lib\/libGKlib.a \/home\/jsb\/.local\/lib\/libparmetis.a -lblas/' /home/jsb/PyBaMM/install_KLU_Sundials/build_sundials/examples/sunlinsol/superludist/CMakeFiles/test_sunlinsol_superludist.dir/link.txt
