from numpy import sqrt, array, prod, diff, isscalar, zeros, ones, reshape, complex128, append
from scipy.sparse import diags, spdiags, kron, eye

from . import *
from .fdfd import *


def sig_w(l, dw, m=4, lnR=-12):
    sig_max = -(m+1)*lnR/(2*eta0*dw)
    return sig_max*(l/dw)**m


def S(l, dw, omega):
    return 1-1j*sig_w(l, dw)/(omega*epsilon0_const)


def create_sfactor(wrange, s, omega, Nw, Nw_pml):

    sfactor_array = ones(Nw, dtype=complex128)

    if Nw_pml < 1:
        return sfactor_array

    hw = diff(wrange)[0]/Nw
    dw = Nw_pml*hw

    for i in range(0, Nw):
        if s is 'f':
            if i <= Nw_pml:
                sfactor_array[i] = S(hw * (Nw_pml - i + 0.5), dw, omega)
            elif i > Nw - Nw_pml:
                sfactor_array[i] = S(hw * (i - (Nw - Nw_pml) - 0.5), dw, omega)
        if s is 'b':
            if i <= Nw_pml:
                sfactor_array[i] = S(hw * (Nw_pml - i + 1), dw, omega)
            elif i > Nw - Nw_pml:
                sfactor_array[i] = S(hw * (i - (Nw - Nw_pml) - 1), dw, omega)

    return sfactor_array


def S_create(omega, N, Npml, xrange, yrange=None, matrix_format='csc'):
    M = prod(N)
    if isscalar(Npml): Npml = array([Npml])

    if len(N) < 2:
        N = append(N,1)
        Npml = append(Npml,0)

    Nx = N[0]
    Nx_pml = Npml[0]
    Ny = N[1]
    Ny_pml = Npml[1]

    # Create the sfactor in each direction and for 'f' and 'b'
    s_vector_x_f = create_sfactor(xrange, 'f', omega, Nx, Nx_pml)
    s_vector_x_b = create_sfactor(xrange, 'b', omega, Nx, Nx_pml)
    s_vector_y_f = create_sfactor(yrange, 'f', omega, Ny, Ny_pml)
    s_vector_y_b = create_sfactor(yrange, 'b', omega, Ny, Ny_pml)

    # Fill the 2D space with layers of appropriate s-factors
    Sx_f_2D = zeros(N, dtype=complex128)
    Sx_b_2D = zeros(N, dtype=complex128)
    Sy_f_2D = zeros(N, dtype=complex128)
    Sy_b_2D = zeros(N, dtype=complex128)

    for i in range(0, Nx):
        Sy_f_2D[i, :] = 1/s_vector_y_f
        Sy_b_2D[i, :] = 1/s_vector_y_b

    for j in range(0, Ny):
        Sx_f_2D[:, j] = 1/s_vector_x_f
        Sx_b_2D[:, j] = 1/s_vector_x_b


    # Reshape the 2D s-factors into a 1D s-array
    Sx_f_vec = reshape(Sx_f_2D, (1, M), order='F')
    Sx_b_vec = reshape(Sx_b_2D, (1, M), order='F')
    Sy_f_vec = reshape(Sy_f_2D, (1, M), order='F')
    Sy_b_vec = reshape(Sy_b_2D, (1, M), order='F')

    # Construct the 1D total s-array into a diagonal matrix
    Sx_f = spdiags(Sx_f_vec, 0, M, M, format=matrix_format)
    Sx_b = spdiags(Sx_b_vec, 0, M, M, format=matrix_format)
    Sy_f = spdiags(Sy_f_vec, 0, M, M, format=matrix_format)
    Sy_b = spdiags(Sy_b_vec, 0, M, M, format=matrix_format)

    return (Sx_f, Sx_b, Sy_f, Sy_b)