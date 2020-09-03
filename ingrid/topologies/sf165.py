"""
SF165.py

Description:
    SNL configuration class.

Created: June 18, 2020

"""
import numpy as np
import matplotlib
import pathlib
try:
    matplotlib.use("TkAgg")
except:
    pass
import matplotlib.pyplot as plt
from utils.topology_utils import Topology
from geometry import Point, Line, Patch, trim_geometry
from collections import OrderedDict


class SF165(Topology):
    def __init__(self, Ingrid_obj, config):
        Topology.__init__(self, Ingrid_obj, config)

        self.ConnexionMap = {
            'A1': {'N': ('A2', 'S')},
            'A2': {'N': ('A3', 'S')},
            'A3': None,

            'B1': {'N': ('B2', 'S'), 'W': ('H1', 'E')},
            'B2': {'N': ('B3', 'S'), 'W': ('H2', 'E')},
            'B3': {'W': ('A3', 'E')},

            'C1': {'N': ('C2', 'S'), 'W': ('B1', 'E')},
            'C2': {'N': ('C3', 'S'), 'W': ('B2', 'E')},
            'C3': {'W': ('B3', 'E')},

            'D1': {'N': ('D2', 'S'), 'W': ('C1', 'E')},
            'D2': {'N': ('D3', 'S'), 'W': ('C2', 'E')},
            'D3': {'W': ('C3', 'E')},

            'E1': {'N': ('E2', 'S'), 'W': ('D1', 'E'), 'E': ('H1', 'W')},
            'E2': {'N': ('E3', 'S'), 'W': ('D2', 'E')},
            'E3': {'W': ('D3', 'E')},

            'F1': {'N': ('F2', 'S'), 'W': ('G1', 'E')},
            'F2': {'N': ('F3', 'S'), 'W': ('E2', 'E')},
            'F3': {'W': ('E3', 'E')},

            'G1': {'N': ('G2', 'S')},
            'G2': {'N': ('G3', 'S')},
            'G3': None,

            'H1': {'N': ('H2', 'S')},
            'H2': {'N': ('H3', 'S'), 'W': ('G2', 'E')},
            'H3': {'W': ('G3', 'E')},

            'I1': {'N': ('I2', 'S'), 'W': ('A1', 'E')},
            'I2': {'N': ('I3', 'S'), 'W': ('A2', 'E')},
            'I3': {'W': ('H3', 'E')}
        }

    def construct_patches(self):
        """
        Draws lines and creates patches for both USN and LSN configurations.

        Patch Labeling Key:
            I: Inner,
            O: Outer,
            DL: Divertor Leg,
            PF: Private Flux,
            T: Top,
            B: Bottom,
            S: Scrape Off Layer,
            C: Core.
        """

        try:
            visual = self.settings['DEBUG']['visual']['patch_map']
        except KeyError:
            visual = False
        try:
            verbose = self.settings['DEBUG']['verbose']['patch_generation']
        except KeyError:
            verbose = False
        try:
            tilt_1 = self.settings['grid_settings']['patch_generation']['tilt_1']
        except KeyError:
            tilt_1 = 0.0
        try:
            tilt_2 = self.settings['grid_settings']['patch_generation']['tilt_2']
        except KeyError:
            tilt_2 = 0.0

        xpt1 = self.LineTracer.NSEW_lookup['xpt1']['coor']
        xpt2 = self.LineTracer.NSEW_lookup['xpt2']['coor']

        magx = np.array([self.settings['grid_settings']['rmagx'] + self.settings['grid_settings']['patch_generation']['rmagx_shift'],
                         self.settings['grid_settings']['zmagx'] + self.settings['grid_settings']['patch_generation']['zmagx_shift']])

        psi_max_west = self.settings['grid_settings']['psi_max_west']
        psi_max_east = self.settings['grid_settings']['psi_max_east']
        psi_core = self.settings['grid_settings']['psi_core']
        psi_pf_1 = self.settings['grid_settings']['psi_pf_1']
        psi_pf_2 = self.settings['grid_settings']['psi_pf_2']
        psi_separatrix_2 = Point(xpt2['center']).psi(self)

        if self.settings['limiter']['use_limiter']:
            WestPlate1 = self.parent.LimiterData.copy()
            WestPlate2 = self.parent.LimiterData.copy()

            EastPlate1 = self.parent.LimiterData.copy()
            EastPlate2 = self.parent.LimiterData.copy()

        else:
            WestPlate1 = Line([Point(i) for i in self.plate_W1])
            WestPlate2 = Line([Point(i) for i in self.plate_W2])

            EastPlate1 = Line([Point(i) for i in self.plate_E1])
            EastPlate2 = Line([Point(i) for i in self.plate_E2])

        # Generate Horizontal Mid-Plane lines
        LHS_Point = Point(magx[0] - 1e6 * np.cos(tilt_1), magx[1] - 1e6 * np.sin(tilt_1))
        RHS_Point = Point(magx[0] + 1e6 * np.cos(tilt_1), magx[1] + 1e6 * np.sin(tilt_1))
        midline_1 = Line([LHS_Point, RHS_Point])
        midline_1.plot()

        LHS_Point = Point(magx[0] - 1e6 * np.cos(tilt_2), magx[1] - 1e6 * np.sin(tilt_2))
        RHS_Point = Point(magx[0] + 1e6 * np.cos(tilt_2), magx[1] + 1e6 * np.sin(tilt_2))
        midline_2 = Line([LHS_Point, RHS_Point])
        # outer_midLine.plot()

        # Generate Vertical Mid-Plane line
        Lower_Point = Point(magx[0], magx[1] - 1e6)
        Upper_Point = Point(magx[0], magx[1] + 1e6)
        topLine = Line([Lower_Point, Upper_Point])

        E1_E = self.LineTracer.draw_line(xpt1['N'], {'psi': psi_core}, option='rho', direction='cw', show_plot=visual, text=verbose)
        H1_W = E1_E.reverse_copy()

        E1_S = self.LineTracer.draw_line(E1_E.p[-1], {'line': midline_2}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        D1_S = self.LineTracer.draw_line(E1_S.p[-1], {'line': topLine}, option='theta', direction='ccw', show_plot=visual, text=verbose)

        B1_S__H1_S = self.LineTracer.draw_line(E1_E.p[-1], {'line': midline_1}, option='theta', direction='cw', show_plot=visual, text=verbose).reverse_copy()
        C1_S = self.LineTracer.draw_line(B1_S__H1_S.p[0], {'line': topLine}, option='theta', direction='cw', show_plot=visual, text=verbose).reverse_copy()

        H1_N__B1_N = self.LineTracer.draw_line(xpt1['NW'], {'line': midline_1}, option='theta', direction='cw', show_plot=visual, text=verbose)

        C1_N = self.LineTracer.draw_line(H1_N__B1_N.p[-1], {'line': topLine}, option='theta', direction='cw', show_plot=visual, text=verbose)
        C2_S = C1_N.reverse_copy()

        E2_S = self.LineTracer.draw_line(xpt1['NE'], {'line': midline_2}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        E1_N = E2_S.reverse_copy()

        D2_S = self.LineTracer.draw_line(E2_S.p[-1], {'line': topLine}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        D1_N = D2_S.reverse_copy()

        H2_E = self.LineTracer.draw_line(xpt2['N'], {'line': H1_N__B1_N}, option='rho', direction='cw', show_plot=visual, text=verbose)
        B2_W = H2_E.reverse_copy()

        H1_N, B1_N = H1_N__B1_N.split(H2_E.p[-1], add_split_point=True)
        H2_S, B2_S = H1_N.reverse_copy(), B1_N.reverse_copy()

        H1_E = self.LineTracer.draw_line(H2_E.p[-1], {'line': B1_S__H1_S}, option='rho', direction='cw', show_plot=visual, text=verbose)
        B1_W = H1_E.reverse_copy()

        B1_S, H1_S = B1_S__H1_S.split(H1_E.p[-1], add_split_point=True)

        F2_W__F3_W = self.LineTracer.draw_line(xpt1['E'], {'psi': psi_max_west}, option='rho', direction='ccw', show_plot=visual, text=verbose)
        B3_W = self.LineTracer.draw_line(xpt2['W'], {'psi': psi_max_west}, option='rho', direction='ccw', show_plot=visual, text=verbose)
        A3_E = B3_W.reverse_copy()

        A3_N = self.LineTracer.draw_line(B3_W.p[-1], {'line': WestPlate2}, option='theta', direction='ccw', show_plot=visual, text=verbose).reverse_copy()
        B3_N = self.LineTracer.draw_line(A3_N.p[-1], {'line': midline_1}, option='theta', direction='cw', show_plot=visual, text=verbose)
        C3_N = self.LineTracer.draw_line(B3_N.p[-1], {'line': topLine}, option='theta', direction='cw', show_plot=visual, text=verbose)

        F3_N = self.LineTracer.draw_line(F2_W__F3_W.p[-1], {'line': EastPlate1}, option='theta', direction='cw', show_plot=visual, text=verbose)
        E3_N = self.LineTracer.draw_line(F3_N.p[0], {'line': midline_2}, option='theta', direction='ccw', show_plot=visual, text=verbose).reverse_copy()
        D3_N = self.LineTracer.draw_line(E3_N.p[0], {'line': topLine}, option='theta', direction='ccw', show_plot=visual, text=verbose).reverse_copy()

        B2_N = self.LineTracer.draw_line(xpt2['NW'], {'line': midline_1}, option='theta', direction='cw', show_plot=visual, text=verbose)
        B3_S = B2_N.reverse_copy()

        C2_N = self.LineTracer.draw_line(B2_N.p[-1], {'line': topLine}, option='theta', direction='cw', show_plot=visual, text=verbose)
        C3_S = C2_N.reverse_copy()

        D2_N = self.LineTracer.draw_line(C2_N.p[-1], {'line': midline_2}, option='theta', direction='cw', show_plot=visual, text=verbose)
        D3_S = D2_N.reverse_copy()

        E2_N = self.LineTracer.draw_line(D2_N.p[-1], {'line': F2_W__F3_W}, option='theta', direction='cw', show_plot=visual, text=verbose)
        E3_S = E2_N.reverse_copy()

        F2_W, F3_W = F2_W__F3_W.split(E2_N.p[-1], add_split_point=True)
        E2_E, E3_E = F2_W.reverse_copy(), F3_W.reverse_copy()

        F2_N = self.LineTracer.draw_line(E2_N.p[-1], {'line': EastPlate1}, option='theta', direction='cw', show_plot=visual, text=verbose)
        F3_S = F2_N.reverse_copy()

        F1_N = self.LineTracer.draw_line(xpt1['SE'], {'line': EastPlate1}, option='theta', direction='cw', show_plot=visual, text=verbose)
        F2_S = F1_N.reverse_copy()

        G1_E = self.LineTracer.draw_line(xpt1['S'], {'psi': psi_pf_1}, option='rho', direction='cw', show_plot=visual, text=verbose)
        F1_W = G1_E.reverse_copy()

        G1_S = self.LineTracer.draw_line(G1_E.p[-1], {'line': WestPlate1}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        F1_S = self.LineTracer.draw_line(G1_E.p[-1], {'line': EastPlate1}, option='theta', direction='cw', show_plot=visual, text=verbose).reverse_copy()

        G2_S = self.LineTracer.draw_line(xpt1['SW'], {'line': WestPlate1}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        G1_N = G2_S.reverse_copy()

        H3_S__G3_S = self.LineTracer.draw_line(xpt2['NE'], {'line': WestPlate1}, option='theta', direction='ccw', show_plot=visual, text=verbose)

        H2_W = self.LineTracer.draw_line(xpt1['W'], {'line': H3_S__G3_S}, option='rho', direction='ccw', show_plot=visual, text=verbose)
        G2_E = H2_W.reverse_copy()

        H3_S, G3_S = H3_S__G3_S.split(H2_W.p[-1], add_split_point=True)
        H2_N, G2_N = H3_S.reverse_copy(), G3_S.reverse_copy()

        I3_W = self.LineTracer.draw_line(xpt2['E'], {'psi': psi_max_east}, option='rho', direction='ccw', show_plot=visual, text=verbose)
        H3_E = I3_W.reverse_copy()

        I3_N = self.LineTracer.draw_line(I3_W.p[-1], {'line': EastPlate2}, option='theta', direction='cw', show_plot=visual, text=verbose)

        G3_N__H3_N = self.LineTracer.draw_line(I3_W.p[-1], {'line': WestPlate1}, option='theta', direction='ccw', show_plot=visual, text=verbose).reverse_copy()

        H3_W = self.LineTracer.draw_line(G2_N.p[-1], {'line': G3_N__H3_N}, option='rho', direction='ccw', show_plot=visual, text=verbose)
        G3_E = H3_W.reverse_copy()

        G3_N, H3_N = G3_N__H3_N.split(H3_W.p[-1], add_split_point=True)

        A2_E__A1_E = self.LineTracer.draw_line(xpt2['S'], {'psi': psi_pf_2}, option='rho', direction='cw', show_plot=visual, text=verbose)
        A2_E, A1_E = A2_E__A1_E.split(A2_E__A1_E.p[len(A2_E__A1_E.p) // 2], add_split_point=True)
        I2_W, I1_W = A2_E.reverse_copy(), A1_E.reverse_copy()

        A1_S = self.LineTracer.draw_line(A1_E.p[-1], {'line': WestPlate2}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        I1_S = self.LineTracer.draw_line(A1_E.p[-1], {'line': EastPlate2}, option='theta', direction='cw', show_plot=visual, text=verbose).reverse_copy()

        A2_S = self.LineTracer.draw_line(A2_E.p[-1], {'line': WestPlate2}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        A1_N = A2_S.reverse_copy()
        I2_S = self.LineTracer.draw_line(A2_E.p[-1], {'line': EastPlate2}, option='theta', direction='cw', show_plot=visual, text=verbose).reverse_copy()
        I1_N = I2_S.reverse_copy()

        A3_S = self.LineTracer.draw_line(xpt2['SW'], {'line': WestPlate2}, option='theta', direction='ccw', show_plot=visual, text=verbose)
        A2_N = A3_S.reverse_copy()

        I3_S = self.LineTracer.draw_line(xpt2['SE'], {'line': EastPlate2}, option='theta', direction='cw', show_plot=visual, text=verbose).reverse_copy()
        I2_N = I3_S.reverse_copy()

        B3_E = self.LineTracer.draw_line(B3_N.p[-1], {'psi_horizontal': (psi_separatrix_2, tilt_1)}, option='z_const', direction='cw', show_plot=visual, text=verbose)

        C3_W = B3_E.reverse_copy()

        B2_E = self.LineTracer.draw_line(B3_E.p[-1], {'psi_horizontal': (1.0, tilt_1)}, option='z_const', direction='cw', show_plot=visual, text=verbose)
        C2_W = B2_E.reverse_copy()

        B1_E = self.LineTracer.draw_line(B2_E.p[-1], {'psi_horizontal': (psi_core, tilt_1)}, option='z_const', direction='cw', show_plot=visual, text=verbose)
        C1_W = B1_E.reverse_copy()

        C3_E = self.LineTracer.draw_line(C3_N.p[-1], {'psi_vertical': psi_separatrix_2}, option='r_const', direction='ccw', show_plot=visual, text=verbose)
        D3_W = C3_E.reverse_copy()

        C2_E = self.LineTracer.draw_line(C2_N.p[-1], {'psi_vertical': 1.0}, option='r_const', direction='ccw', show_plot=visual, text=verbose)
        D2_W = C2_E.reverse_copy()

        C1_E = self.LineTracer.draw_line(C1_N.p[-1], {'psi_vertical': psi_core}, option='r_const', direction='ccw', show_plot=visual, text=verbose)
        D1_W = C1_E.reverse_copy()

        D3_E = self.LineTracer.draw_line(D3_N.p[-1], {'psi_horizontal': (psi_separatrix_2, tilt_2)}, option='z_const', direction='ccw', show_plot=visual, text=verbose)
        E3_W = D3_E.reverse_copy()

        D2_E = self.LineTracer.draw_line(D3_E.p[-1], {'psi_horizontal': (1.0, tilt_2)}, option='z_const', direction='ccw', show_plot=visual, text=verbose)
        E2_W = D2_E.reverse_copy()

        D1_E = self.LineTracer.draw_line(D2_E.p[-1], {'psi_horizontal': (psi_core, tilt_2)}, option='z_const', direction='ccw', show_plot=visual, text=verbose)
        E1_W = D1_E.reverse_copy()

        A1_W = trim_geometry(WestPlate2, A1_S.p[-1], A1_N.p[0])
        A2_W = trim_geometry(WestPlate2, A2_S.p[-1], A2_N.p[0])
        A3_W = trim_geometry(WestPlate2, A3_S.p[-1], A3_N.p[0])

        F1_E = trim_geometry(EastPlate1, F1_N.p[-1], F1_S.p[0])
        F2_E = trim_geometry(EastPlate1, F2_N.p[-1], F2_S.p[0])
        F3_E = trim_geometry(EastPlate1, F3_N.p[-1], F3_S.p[0])

        I1_E = trim_geometry(WestPlate1, I1_N.p[-1], I1_S.p[0])
        I2_E = trim_geometry(WestPlate1, I2_N.p[-1], I2_S.p[0])
        I3_E = trim_geometry(WestPlate1, I3_N.p[-1], I3_S.p[0])

        G1_W = trim_geometry(EastPlate2, G1_S.p[-1], G1_N.p[0])
        G2_W = trim_geometry(EastPlate2, G2_S.p[-1], G2_N.p[0])
        G3_W = trim_geometry(EastPlate2, G3_S.p[-1], G3_N.p[0])

        # ============== Patch A1 ==============
        A1 = Patch([A1_N, A1_E, A1_S, A1_W], patchName='A1', platePatch=True, plateLocation='W')
        # ============== Patch A2 ==============
        A2 = Patch([A2_N, A2_E, A2_S, A2_W], patchName='A2', platePatch=True, plateLocation='W')
        # ============== Patch A3 ==============
        A3 = Patch([A3_N, A3_E, A3_S, A3_W], patchName='A3', platePatch=True, plateLocation='W')

        # ============== Patch B1 ==============
        B1 = Patch([B1_N, B1_E, B1_S, B1_W], patchName='B1')
        # ============== Patch B2 ==============
        B2 = Patch([B2_N, B2_E, B2_S, B2_W], patchName='B2')
        # ============== Patch B3 ==============
        B3 = Patch([B3_N, B3_E, B3_S, B3_W], patchName='B3')

        # ============== Patch C1 ==============
        C1 = Patch([C1_N, C1_E, C1_S, C1_W], patchName='C1')
        # ============== Patch C2 ==============
        C2 = Patch([C2_N, C2_E, C2_S, C2_W], patchName='C2')
        # ============== Patch C3 ==============
        C3 = Patch([C3_N, C3_E, C3_S, C3_W], patchName='C3')

        # ============== Patch D1 ==============
        D1 = Patch([D1_N, D1_E, D1_S, D1_W], patchName='D1')
        # ============== Patch D2 ==============
        D2 = Patch([D2_N, D2_E, D2_S, D2_W], patchName='D2')
        # ============== Patch D3 ==============
        D3 = Patch([D3_N, D3_E, D3_S, D3_W], patchName='D3')

        # ============== Patch E1 ==============
        E1 = Patch([E1_N, E1_E, E1_S, E1_W], patchName='E1')
        # ============== Patch E2 ==============
        E2 = Patch([E2_N, E2_E, E2_S, E2_W], patchName='E2')
        # ============== Patch E3 ==============
        E3 = Patch([E3_N, E3_E, E3_S, E3_W], patchName='E3')

        # ============== Patch F1 ==============
        F1 = Patch([F1_N, F1_E, F1_S, F1_W], patchName='F1', platePatch=True, plateLocation='E')
        # ============== Patch F2 ==============
        F2 = Patch([F2_N, F2_E, F2_S, F2_W], patchName='F2', platePatch=True, plateLocation='E')
        # ============== Patch F3 ==============
        F3 = Patch([F3_N, F3_E, F3_S, F3_W], patchName='F3', platePatch=True, plateLocation='E')

        # ============== Patch G1 ==============
        G1 = Patch([G1_N, G1_E, G1_S, G1_W], patchName='G1', platePatch=True, plateLocation='W')
        # ============== Patch G2 ==============
        G2 = Patch([G2_N, G2_E, G2_S, G2_W], patchName='G2', platePatch=True, plateLocation='W')
        # ============== Patch G3 ==============
        G3 = Patch([G3_N, G3_E, G3_S, G3_W], patchName='G3', platePatch=True, plateLocation='W')

        # ============== Patch H1 ==============
        H1 = Patch([H1_N, H1_E, H1_S, H1_W], patchName='H1')
        # ============== Patch H2 ==============
        H2 = Patch([H2_N, H2_E, H2_S, H2_W], patchName='H2')
        # ============== Patch H3 ==============
        H3 = Patch([H3_N, H3_E, H3_S, H3_W], patchName='H3')

        # ============== Patch I1 ==============
        I1 = Patch([I1_N, I1_E, I1_S, I1_W], patchName='I1', platePatch=True, plateLocation='E')
        # ============== Patch I2 ==============
        I2 = Patch([I2_N, I2_E, I2_S, I2_W], patchName='I2', platePatch=True, plateLocation='E')
        # ============== Patch I3 ==============
        I3 = Patch([I3_N, I3_E, I3_S, I3_W], patchName='I3', platePatch=True, plateLocation='E')

        patches = [A3, A2, A1, B3, B2, B1, C3, C2, C1, D3, D2, D1, E3, E2, E1,
                   F3, F2, F1, G3, G2, G1, H3, H2, H1, I3, I2, I1]

        self.patches = {}
        for patch in patches:
            patch.parent = self
            patch.PatchTagMap = self.PatchTagMap
            self.patches[patch.patchName] = patch
        self.OrderPatches()

    def OrderPatches(self):

        patches = [
            'A3', 'B3', 'C3', 'D3', 'E3', 'F3', 'G3', 'H3', 'I3',
            'A2', 'I2', 'G2', 'H2', 'B2', 'C2', 'D2', 'E2', 'F2',
            'A1', 'I1', 'G1', 'F1', 'H1', 'B1', 'C1', 'D1', 'E1'
        ]

        self.patches = OrderedDict([(pname, self.patches[pname]) for pname in patches])

    def AdjustPatch(self, patch):
        xpt1 = Point(self.LineTracer.NSEW_lookup['xpt1']['coor']['center'])
        xpt2 = Point(self.LineTracer.NSEW_lookup['xpt2']['coor']['center'])

        tag = patch.get_tag()
        if tag == 'A3':
            patch.adjust_corner(xpt2, 'SE')
        elif tag == 'A2':
            patch.adjust_corner(xpt2, 'NE')
        elif tag == 'B3':
            patch.adjust_corner(xpt2, 'SW')
        elif tag == 'B2':
            patch.adjust_corner(xpt2, 'NW')
        elif tag == 'E2':
            patch.adjust_corner(xpt1, 'SE')
        elif tag == 'E1':
            patch.adjust_corner(xpt1, 'NE')
        elif tag == 'F2':
            patch.adjust_corner(xpt1, 'SW')
        elif tag == 'F1':
            patch.adjust_corner(xpt1, 'NW')
        elif tag == 'G1':
            patch.adjust_corner(xpt1, 'NE')
        elif tag == 'G2':
            patch.adjust_corner(xpt1, 'SE')
        elif tag == 'H1':
            patch.adjust_corner(xpt1, 'NW')
        elif tag == 'H2':
            patch.adjust_corner(xpt1, 'SW')
            patch.adjust_corner(xpt2, 'NE')
        elif tag == 'H3':
            patch.adjust_corner(xpt2, 'SE')
        elif tag == 'I3':
            patch.adjust_corner(xpt2, 'SW')
        elif tag == 'I2':
            patch.adjust_corner(xpt2, 'NW')

    def GroupPatches(self):
        # p = self.patches
        # self.PatchGroup = {'SOL' : [],
        # 'CORE' : (p['ICB'], p['ICT'], p['OCT'], p['OCB']),
        # 'PF' : (p['IPF'], p['OPF'])}
        pass

    def set_gridue(self):
        """
        set_gridue:
            Prepares 'self.gridue_settings' dictionary with required data.
            The self.gridue_settings attribute is used to write a gridue
            formatted file
        Parameters:
            N/A
        Return:
            N/A
        """

        ixlb = 0
        ixrb = len(self.rm) - 2

        nxm = len(self.rm) - 2
        nym = len(self.rm[0]) - 2
        iyseparatrix1 = self.patches['A1'].nrad + self.patches['A2'].nrad - 2
        iyseparatrix2 = self.patches['E1'].nrad - 1
        iyseparatrix3 = iyseparatrix2
        iyseparatrix4 = iyseparatrix1

        ix_plate1 = 0
        ix_cut1 = self.patches['A1'].npol - 1

        ix_cut2 = 0
        for alpha in ['A', 'B', 'C', 'D', 'E']:
            ix_cut2 += self.patches[alpha + '1'].npol - 1

        ix_plate2 = 0
        for alpha in ['A', 'B', 'C', 'D', 'E', 'F']:
            ix_plate2 += self.patches[alpha + '3'].npol - 1

        ix_plate3 = ix_plate2 + 2

        ix_cut3 = 0
        for alpha in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            ix_cut3 += self.patches[alpha + '1'].npol - 1
        ix_cut3 += 2

        ix_cut4 = 0
        for alpha in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            ix_cut4 += self.patches[alpha + '2'].npol - 1
        ix_cut4 += 2

        ix_plate4 = 0
        for alpha in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
            ix_plate4 += self.patches[alpha + '1'].npol - 1
        ix_plate4 += 2

        psi = np.zeros((nxm + 2, nym + 2, 5), order='F')
        br = np.zeros((nxm + 2, nym + 2, 5), order='F')
        bz = np.zeros((nxm + 2, nym + 2, 5), order='F')
        bpol = np.zeros((nxm + 2, nym + 2, 5), order='F')
        bphi = np.zeros((nxm + 2, nym + 2, 5), order='F')
        b = np.zeros((nxm + 2, nym + 2, 5), order='F')

        rm = self.rm
        zm = self.zm
        rb_prod = self.PsiUNorm.rcenter * self.PsiUNorm.bcenter

        for i in range(len(b)):
            for j in range(len(b[0])):
                for k in range(5):
                    _r = rm[i][j][k]
                    _z = zm[i][j][k]

                    _psi = self.PsiUNorm.get_psi(_r, _z)
                    _br = self.PsiUNorm.get_psi(_r, _z, tag='vz') / _r
                    _bz = -self.PsiUNorm.get_psi(_r, _z, tag='vr') / _r
                    _bpol = np.sqrt(_br ** 2 + _bz ** 2)
                    _bphi = rb_prod / _r
                    _b = np.sqrt(_bpol ** 2 + _bphi ** 2)

                    psi[i][j][k] = _psi
                    br[i][j][k] = _br
                    bz[i][j][k] = _bz
                    bpol[i][j][k] = _bpol
                    bphi[i][j][k] = _bphi
                    b[i][j][k] = _b

        self.gridue_settings = {'nxm': nxm, 'nym': nym, 'iyseparatrix1': iyseparatrix1, 'iyseparatrix2': iyseparatrix2,
                                'ix_plate1': ix_plate1, 'ix_cut1': ix_cut1, 'ix_cut2': ix_cut2, 'ix_plate2': ix_plate2, 'iyseparatrix3': iyseparatrix3,
                                'iyseparatrix4': iyseparatrix4, 'ix_plate3': ix_plate3, 'ix_cut3': ix_cut3, 'ix_cut4': ix_cut4, 'ix_plate4': ix_plate4,
                                'rm': self.rm, 'zm': self.zm, 'psi': psi, 'br': br, 'bz': bz, 'bpol': bpol, 'bphi': bphi, 'b': b, '_FILLER_': -1}
