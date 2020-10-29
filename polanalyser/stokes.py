import cv2
import numpy as np
from numba import njit

import warnings
from numba import NumbaPerformanceWarning
warnings.simplefilter('ignore', NumbaPerformanceWarning) # Ignore numba warning of "NumbaPerformanceWarning: The keyword argument 'parallel=True' was specified but no transformation for parallel execution was possible."

from .mueller import polarizer

def calcStokes(I, M):
    """
    Calculate stokes vector from observed intensity and mueller matrix

    Parameters
    ----------
    I : np.ndarray
      Observed intensity
    M : np.ndarray
      Mueller matrix

    Returns
    -------
    S : np.ndarray
      Stokes vector
    """
    A = M[..., 0, :]
    A_pinv = np.linalg.pinv(A)
    S = np.tensordot(A_pinv, I, axes=(1,-1)) # (3, ...)
    S = np.moveaxis(S, 0, -1) # (..., 3)
    return S

def calcLinearStokes(I, theta):
    """
    Calculate only linear polarization stokes vector from observed intensity and linear polarizer angle
    
    Parameters
    ----------
    I : np.ndarray
      Observed intensity
    theta : np.ndarray
      Polarizer angles

    Returns
    -------
    S : np.ndarray
      Stokes vector
    """
    M = polarizer(theta)[..., :3, :3]
    return calcStokes(I, M)

@njit(parallel=True, cache=True)
def cvtStokesToImax(img_stokes):
    """
    Convert stokes vector image to Imax image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_Imax : np.ndarray, (height, width)
        Imax image
    """
    S0 = img_stokes[..., 0]
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    return (S0+np.sqrt(S1**2+S2**2))*0.5

@njit(parallel=True, cache=True)
def cvtStokesToImin(img_stokes):
    """
    Convert stokes vector image to Imin image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_Imin : np.ndarray, (height, width)
        Imin image
    """
    S0 = img_stokes[..., 0]
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    return (S0-np.sqrt(S1**2+S2**2))*0.5

@njit(parallel=True, cache=True)
def cvtStokesToDoLP(img_stokes):
    """
    Convert stokes vector image to DoLP (Degree of Linear Polarization) image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_DoLP : np.ndarray, (height, width)
        DoLP image
    """
    S0 = img_stokes[..., 0]
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    return np.sqrt(S1**2+S2**2)/S0

@njit(parallel=True, cache=True)
def cvtStokesToAoLP(img_stokes):
    """
    Convert stokes vector image to AoLP (Angle of Linear Polarization) image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_AoLP : np.ndarray, (height, width)
        AoLP image
    """
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    return np.mod(0.5*np.arctan2(S2, S1), np.pi)

@njit(parallel=True, cache=True)
def cvtStokesToIntensity(img_stokes):
    """
    Convert stokes vector image to intensity image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_intensity : np.ndarray, (height, width)
        Intensity image
    """
    S0 = img_stokes[..., 0]
    return S0*0.5

@njit(parallel=True, cache=True)
def cvtStokesToDiffuse(img_stokes):
    """
    Convert stokes vector image to diffuse image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_diffuse : np.ndarray, (height, width)
        Diffuse image
    """
    Imin = cvtStokesToImin(img_stokes)
    return 1.0*Imin

@njit(parallel=True, cache=True)
def cvtStokesToSpecular(img_stokes):
    """
    Convert stokes vector image to specular image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_specular : np.ndarray, (height, width)
        Specular image
    """
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    return np.sqrt(S1**2+S2**2) #same as Imax-Imin

@njit(parallel=True, cache=True)
def cvtStokesToDoP(img_stokes):
    """
    Convert stokes vector image to DoP (Degree of Polarization) image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_DoP : np.ndarray, (height, width)
        DoP image
    """
    S0 = img_stokes[..., 0]
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    S3 = img_stokes[..., 3]
    return np.sqrt(S1**2+S2**2+S3**2)/S0

@njit(parallel=True, cache=True)
def cvtStokesToEllipticityAngle(img_stokes):
    """
    Convert stokes vector image to ellipticity angle image

    Parameters
    ----------
    img_stokes : np.ndarray, (height, width, 3)
        Stokes vector image

    Returns
    -------
    img_EllipticityAngle : np.ndarray, (height, width)
        ellipticity angle image (-pi/4 ~ pi/4)
    """
    S1 = img_stokes[..., 1]
    S2 = img_stokes[..., 2]
    S3 = img_stokes[..., 3]
    return 0.5*np.arctan2(S3, np.sqrt(S1**2+S2**2))


def applyColorToAoLP(img_AoLP, saturation=1.0, value=1.0):
    """
    Apply color map to AoLP image
    The color map is based on HSV

    Parameters
    ----------
    img_AoLP : np.ndarray, (height, width)
        AoLP image. The range is from 0.0 to pi.
    
    saturation : float or np.ndarray, (height, width)
        Saturation part (optional).
        If you pass DoLP image (img_DoLP) as an argument, you can modulate it by DoLP.

    value : float or np.ndarray, (height, width)
        Value parr (optional).
        If you pass DoLP image (img_DoLP) as an argument, you can modulate it by DoLP.
    """
    img_ones = np.ones_like(img_AoLP)

    img_hue = (np.mod(img_AoLP, np.pi)/np.pi*179).astype(np.uint8) # 0~pi -> 0~179
    img_saturation = np.clip(img_ones*saturation*255, 0, 255).astype(np.uint8)
    img_value = np.clip(img_ones*value*255, 0, 255).astype(np.uint8)
    
    img_hsv = cv2.merge([img_hue, img_saturation, img_value])
    img_bgr = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
    return img_bgr
