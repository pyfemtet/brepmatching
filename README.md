# BRepMatching-Femtet

## About This Library
BRepMatching-Femtet is a library that assigns permanent IDs to the topology of two Parasolid files and estimates their correspondence. This library is derived from [BRepMatching](https://github.com/deGravity/BRepMatching) (written by deGravity (Ben Jones)) that is the implementation of the paper[1].


## Installation
You can install it via pip:

```pip install brepmatching-femtet```

Please note that a licensed version of Femtet is required for this library to function properly.


## License
This library is licensed under the MIT License.
It utilizes Eigen 3.4.0, which can be obtained from [this site](https://eigen.tuxfamily.org/index.php?title=Main_Page).


## Usage

```python
from brepmatching.pyfemtet_scripts import Predictor
from win32com.client import Dispatch

# get Femtet control
Femtet = Dispatch('FemtetMacro.Femtet')

# initialize (create temporary foldere and child process)
predictor = Predictor(Femtet)

# predict
id_map: dict = predictor.predict(
    'orig.x_t',
    'var.x_t',
)

# finalize (delete temporary folder and terminate child process)
del predictor

```

## References
[1] B-rep Matching for Collaborating Across CAD Systems,  
[https://doi.org/10.48550/arXiv.2306.03169](https://doi.org/10.48550/arXiv.2306.03169)
