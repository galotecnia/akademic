#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Akademic: Herramienta para el control del alumnado en centros escolares.

    Copyright (C) 2010  Galotecnia Redes Sistemas y Servicios S.L.L. <info@galotecnia.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from django.core.management import setup_environ
import settings

setup_environ(settings)

import sys
from padres.models import Padre
from notificacion.models import Notificacion

verificados_con_repeticiones = [15, 16, 17, 18, 21, 22, 24, 25, 26, 28, 30, 34, 46, 47, 60, 61, 64,
     69, 76, 78, 80, 81, 84, 94, 95, 96, 97, 98, 99, 106, 108, 112, 113,
     118, 121, 122, 128, 138, 139, 143, 146, 147, 151, 155, 161, 162, 163,
     168, 169, 170, 171, 186, 187, 191, 193, 199, 201, 204, 205, 206, 207,
     209, 213, 214, 223, 224, 235, 238, 239, 240, 244, 246, 248, 249, 250,
     251, 252, 254, 255, 256, 258, 259, 260, 265, 266, 273, 275, 276, 277,
     278, 280, 282, 283, 284, 290, 291, 296, 297, 307, 316, 317, 319, 323,
     324, 335, 340, 341, 355, 356, 360, 361, 377, 384, 385, 407, 408, 409,
     410, 411, 412, 419, 426, 429, 434, 435, 439, 440, 444, 445, 448,
     452, 453, 455, 456, 457, 458, 459, 460, 463, 464, 465, 466, 468, 469,
     472, 473, 476, 477, 480, 481, 482, 486, 490, 491, 493, 512, 550, 580,
     581, 604, 628, 629, 643, 655, 734, 742, 750, 753, 754, 755, 760, 761,
     766, 768, 777, 778, 779, 784, 785, 787, 792, 793, 800, 801, 803, 804,
     805, 807, 808, 809, 810, 815, 816, 817, 818, 819, 820, 825, 827, 828,
     841, 842, 843, 844, 845, 846, 849, 852, 927, 1003, 1004, 1061, 1063,
     1064, 1065, 1068, 1069, 1072, 1073, 1075, 1076, 1077, 1078, 1083, 1084,
     1085, 1087, 1088, 1089, 1092, 1095, 1096, 1097, 1099, 1100, 1101, 1102,
     1103, 1107, 1108, 1109, 1110, 1112, 1114, 1115, 1116, 1119, 1126,
     1142, 1147, 1151, 1153, 1156, 1180, 1188, 1190, 1207, 1208, 1211, 1212,
     1242, 1243, 1247, 1248, 1267, 1268, 1286, 1296, 1315, 1321, 1322, 1431,
     1432, 1449, 1450, 1494, 1495, 1498, 1499, 1500, 1501, 1503, 1505, 1506,
     1507, 1509, 1511, 1512, 1513, 1514, 1516, 1518, 1521, 1522, 1523, 1527,
     1528, 1529, 1533, 1534, 1535, 1536, 1537, 1538, 1539, 1540, 1541, 1559,
     1562, 1563, 1565, 1587, 1591, 1592, 1601, 1603, 1605, 1606, 1607, 1613,
     1615, 1617, 1618, 1620, 1621, 1622, 1623, 1624, 1625, 1626, 1627, 1628,
     1634, 1635, 1637, 1638, 1641, 1642, 1644, 1645, 1647, 1648, 1649, 1652,
     1653, 1662, 1663, 1664, 1665, 1667, 1668, 1669, 1670, 1671, 1673, 1676,
     1677, 1684, 1685, 1686, 1699, 1706, 1707, 1708, 1710, 1711, 1712,
     1713, 1715, 1717, 1718, 1719, 1720, 1721, 1723, 1724, 1725, 1726, 1727,
     1728, 1729, 1733, 1735, 1737, 1738, 1739, 1740, 1741, 1742, 1743, 1744,
     1745, 1746, 1747, 1749, 1750, 1751, 1752, 1753, 1754, 1756, 1758, 1759,
     1760, 1763, 1765, 1766, 1767, 1768, 1770, 1772, 1774, 1787, 1788, 1802,
     1803, 1804, 1805, 1806, 1807, 1808, 1810, 1811, 1812, 1816, 1817, 1818,
     1819, 1822, 1823, 1826, 1830, 1832, 1834, 1835, 1836, 1838, 1839, 1841,
     1842, 1843, 1844, 1846, 1847, 1849, 1850, 1851, 1852, 1853, 1854, 1855,
     1857, 1858, 1862, 1864, 1866, 1869, 1871, 1872, 1874, 1875, 1883, 1884,
     1896, 1912, 1913, 1914, 1915, 1918, 1919, 1920, 1938, 1939, 1952, 1955,
     1957, 1962, 1963, 1964, 1965, 1966, 1968, 1969, 1970, 1978, 1979, 1980,
     1981, 1982, 1983, 1985, 1987, 1988, 1989, 1992, 1993, 1995, 2003, 2006,
     2007, 2008, 2009, 2011, 2012, 2024, 2027, 2028, 2037, 2038, 2039,
     2040, 2044, 2045, 2046, 2049, 2050, 2051, 2052, 2057, 2058, 2063, 2064,
     2065, 2066, 2067, 2068, 2071, 2072, 2073, 2074, 2077, 2086, 2087, 2098,
     2099, 2101, 2102, 2103, 2104, 2105, 2106, 2108, 2109, 2111, 2112, 2113,
     2115, 2116, 2117, 2118, 2119, 2120, 2122, 2123, 2126, 2127, 2128, 2129,
     2131, 2132, 2133, 2134, 2136, 2137, 2138, 2139, 2140, 2142, 2143, 2144,
     2145, 2146, 2148, 2149, 2150, 2151, 2153, 2154, 2157, 2158, 2163, 2164,
     2165, 2166, 2168, 2170, 2171, 2172, 2186, 2189, 2193, 2194, 2195,
     2201, 2202, 2204, 2205, 2207, 2208, 2210, 2212, 2213, 2214, 2215, 2219,
     2220, 2221, 2222, 2223, 2225, 2226, 2227, 2229, 2230, 2231, 2233, 2234,
     2235, 2236, 2237, 2238, 2240, 2241, 2242, 2243, 2244, 2245, 2246, 2247,
     2248, 2249, 2250, 2252, 2254, 2255, 2256, 2257, 2258, 2259, 2260, 2261,
     2262, 2263, 2264, 2265, 2266, 2268, 2269, 2270, 2272, 2273, 2274, 2275,
     2277, 2278, 2279, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288,
     2289, 2290, 2291, 2292, 2293, 2294, 2295, 2296, 2297, 2298, 2299, 2301,
     2302, 2303, 2304, 2311, 2312, 2313, 2315, 2318, 2320, 2326, 2327, 2328,
     2329, 2330, 2334, 2336, 2337, 2338, 2352, 2356, 2364, 2368, 2376, 2378,
     2379, 2380, 2385, 2386, 2387, 2389, 2390, 2410, 2476, 2489, 2490, 2491,
     2503, 2504, 2507, 2508, 2514, 2516, 2525, 2579, 2580, 2618, 2619, 2620,
     2637, 2638, 2642, 2644, 2645, 2649, 2652, 2658, 2661, 2664, 2678,
     2679, 2735, 2740, 2741, 2748, 2749, 2752, 2753, 2756, 2759]

verificados = []
for id in verificados_con_repeticiones:
	if not id in verificados:
		verificados.append(id)
		continue
	print "- el padre id=%d estaba repetido" % id
print

print "Padres verificados via post: ", len(verificados)
print "Padres con verificado = True: ", Padre.objects.filter(verificado__isnull=False).count()
print "Notifiaciones que comienzan con 'Estimado': ", Notificacion.objects.filter(texto__texto__startswith='Estimado').count()
print 

for id in verificados:
	p = Padre.objects.get(pk=id)
	
	errores = []
	if p.verificado is None: 
		errores.append("no tiene el objeto padre verificado")
	if Notificacion.objects.filter(padre__pk=id, texto__texto__startswith="Estimado").count() == 0:
		errores.append("no tiene sms con la clave")
	if p.get_hijos().count() == 0:
		errores.append("no tiene hijos")
	if p.persona.tlf_movil() == "":
		errores.append("no tiene telefono")
	
	if len(errores) > 0:	
		print "- el Padre.objects.get(pk=%d) (%s)" % (id, p)
		for e in errores:
			print "   * %s" % e
		#for h in p.get_matriculas_hijos():
		for h in p.get_hijos():
			try:
				grupo = h.getGrupo().grupo
			except:
				grupo = "PROBLEMA"
			print "     + Alumno.objects.get(pk=%d) (%s)" % (h.pk, h)
			print "       %d asignaturas, %s" % (h.getAsignaturas().count(), grupo)
			if h.padre: 
				print u"       padre: '%s' (movil: '%s')" % (h.padre, h.padre.persona.tlf_movil())
			else:
				print u"       no tiene padre"
			if h.madre:
				print u"       madre: '%s' (movil: '%s')" % (h.madre, h.madre.persona.tlf_movil())
			else:
				print u"       no tiene madre"

		print 
print

