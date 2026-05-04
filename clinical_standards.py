"""
Registry of standardized veterinary medical parameters and reference ranges.
Source: Estandarización de Parámetros Veterinarios Máquinas.md
"""

from typing import Dict, Any, Optional

# Master Registry of Veterinary Standards
VETERINARY_STANDARDS: Dict[str, Dict[str, Any]] = {
    # --- RED SERIES (CBC) ---
    'RBC': {
        'name': 'Conteo de Glóbulos Rojos',
        'unit': 'x10^6/µL',
        'ranges': {
            'canine': {'min': 4.95, 'max': 7.87},
            'feline': {'min': 5.0, 'max': 10.0}
        }
    },
    'HGB': {
        'name': 'Hemoglobina',
        'unit': 'g/dL',
        'ranges': {
            'canine': {'min': 11.9, 'max': 18.9},
            'feline': {'min': 9.8, 'max': 15.4}
        }
    },
    'HCT': {
        'name': 'Hematocrito',
        'unit': '%',
        'ranges': {
            'canine': {'min': 35.0, 'max': 57.0},
            'feline': {'min': 30.0, 'max': 45.0}
        }
    },
    'MCV': {
        'name': 'Volumen Corpuscular Medio',
        'unit': 'fL',
        'ranges': {
            'canine': {'min': 66.0, 'max': 77.0},
            'feline': {'min': 39.0, 'max': 55.0}
        }
    },
    'MCH': {
        'name': 'Hemoglobina Corpuscular Media',
        'unit': 'pg',
        'ranges': {
            'canine': {'min': 21.0, 'max': 26.2},
            'feline': {'min': 13.0, 'max': 17.0}
        }
    },
    'MCHC': {
        'name': 'Concentración de HGB Corpuscular Media',
        'unit': 'g/dL',
        'ranges': {
            'canine': {'min': 32.0, 'max': 36.3},
            'feline': {'min': 30.0, 'max': 36.0}
        }
    },
    'RDW-CV': {
        'name': 'Ancho de Distribución Eritrocitaria (CV)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 12.0, 'max': 17.0},
            'feline': {'min': 14.0, 'max': 18.0}
        }
    },
    'RDW-SD': {
        'name': 'Ancho de Distribución Eritrocitaria (SD)',
        'unit': 'fL',
        'ranges': {
            'canine': {'min': 35.0, 'max': 50.0},
            'feline': {'min': 30.0, 'max': 45.0}
        }
    },
    'HDW-CV': {
        'name': 'Ancho de Distribución de Hemoglobina (CV)',
        'unit': '%',
        'ranges': {
            'canine': None,  # Variable según perfil
            'feline': None
        }
    },
    'HDW-SD': {
        'name': 'Ancho de Distribución de Hemoglobina (SD)',
        'unit': 'pg',
        'ranges': {
            'canine': None,  # Variable según perfil
            'feline': None
        }
    },

    # --- ADVANCED MORPHOLOGY / REGENERATION ---
    'RET#': {
        'name': 'Reticulocitos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 80.0},
            'feline': {'min': 0.0, 'max': 60.0}
        }
    },
    'RET%': {
        'name': 'Reticulocitos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 1.0},
            'feline': {'min': 0.0, 'max': 0.6}
        }
    },
    'SPH#': {
        'name': 'Esferocitos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0}, # Ausente
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'SPH%': {
        'name': 'Esferocitos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'ETG#': {
        'name': 'Células Diana / Codocitos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0}, # Ausente (0 - Raro)
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'ETG%': {
        'name': 'Células Diana (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },

    # --- WHITE SERIES (CBC 7-PART) ---
    'WBC': {
        'name': 'Conteo Total de Leucocitos',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 5.0, 'max': 14.1},
            'feline': {'min': 5.5, 'max': 19.5}
        }
    },
    'NEU#': {
        'name': 'Neutrófilos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 2.9, 'max': 12.0},
            'feline': {'min': 2.5, 'max': 12.5}
        }
    },
    'NEU%': {
        'name': 'Neutrófilos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 58.0, 'max': 85.0},
            'feline': {'min': 45.0, 'max': 64.0}
        }
    },
    'NST#': {
        'name': 'Neutrófilos en Banda (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.3},
            'feline': {'min': 0.0, 'max': 0.3}
        }
    },
    'NST/WBC%': {
        'name': 'Bandas / Total WBC',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 3.0},
            'feline': {'min': 0.0, 'max': 2.0}
        }
    },
    'NST/NEU%': {
        'name': 'Bandas / Neutrófilos',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 5.0},
            'feline': {'min': 0.0, 'max': 5.0}
        }
    },
    'NSG#': {
        'name': 'Neutrófilos Gigantes/Inmaduros (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0}, # Ausente
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'NSG/WBC%': {
        'name': 'Neutrófilos Gigantes / WBC',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'NSH#': {
        'name': 'Neutrófilos Hipersegmentados (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.00, 'max': 0.40},
            'feline': {'min': 0.00, 'max': 0.30}
        }
    },
    'NSH/WBC%': {
        'name': 'Hipersegmentados / WBC',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 2.0},
            'feline': {'min': 0.0, 'max': 2.0}
        }
    },
    'NSH/NEU%': {
        'name': 'Hipersegmentados / Neutrófilos',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 5.0},
            'feline': {'min': 0.0, 'max': 5.0}
        }
    },
    'LYMP#': {
        'name': 'Linfocitos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 1.0, 'max': 4.8},
            'feline': {'min': 1.5, 'max': 7.0}
        }
    },
    'LYM#': {
        'name': 'Linfocitos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 1.0, 'max': 4.8},
            'feline': {'min': 1.5, 'max': 7.0}
        }
    },
    'LYMP%': {
        'name': 'Linfocitos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 12.0, 'max': 30.0},
            'feline': {'min': 20.0, 'max': 45.0}
        }
    },
    'MON#': {
        'name': 'Monocitos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.1, 'max': 1.4},
            'feline': {'min': 0.1, 'max': 0.9}
        }
    },
    'MON%': {
        'name': 'Monocitos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 2.0, 'max': 10.0},
            'feline': {'min': 1.0, 'max': 5.0}
        }
    },
    'EOS#': {
        'name': 'Eosinófilos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.1, 'max': 1.3},
            'feline': {'min': 0.1, 'max': 1.5}
        }
    },
    'EOS%': {
        'name': 'Eosinófilos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 2.0, 'max': 10.0},
            'feline': {'min': 2.0, 'max': 12.0}
        }
    },
    'BAS#': {
        'name': 'Basófilos (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.00, 'max': 0.10},
            'feline': {'min': 0.00, 'max': 0.10}
        }
    },
    'BAS%': {
        'name': 'Basófilos (Porcentaje)',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 1.0},
            'feline': {'min': 0.0, 'max': 1.0}
        }
    },

    # --- PLATELETS ---
    'PLT': {
        'name': 'Conteo de Plaquetas',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 211.0, 'max': 621.0},
            'feline': {'min': 300.0, 'max': 800.0}
        }
    },
    'MPV': {
        'name': 'Volumen Plaquetario Medio',
        'unit': 'fL',
        'ranges': {
            'canine': {'min': 6.1, 'max': 10.1},
            'feline': {'min': 12.0, 'max': 18.0}
        }
    },
    'PDW': {
        'name': 'Ancho de Distribución Plaquetaria',
        'unit': '%',
        'ranges': {
            'canine': None, # Variable
            'feline': None
        }
    },
    'PCT': {
        'name': 'Plaquetocrito',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.15, 'max': 0.50},
            'feline': {'min': 0.15, 'max': 0.50}
        }
    },
    'APLT#': {
        'name': 'Plaquetas Agregadas (Absoluto)',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 0.00, 'max': 0.15}, # Ausente/Bajo
            'feline': {'min': 0.00, 'max': 0.15}  # Variable in vitro
        }
    },
    'P-LCR': {
        'name': 'Ratio de Células Grandes',
        'unit': '%',
        'ranges': {
            'canine': {'min': 0.0, 'max': 5.0},
            'feline': {'min': 0.0, 'max': 10.0}
        }
    },
    'P-LCC': {
        'name': 'Conteo de Células Grandes',
        'unit': 'x10^3/µL',
        'ranges': {
            'canine': {'min': 7.00, 'max': 20.00},
            'feline': {'min': 7.00, 'max': 20.00}
        }
    },

    # --- IMMUNOASSAYS ---
    'cCRP': {
        'name': 'Proteína C Reactiva Canina',
        'unit': 'mg/L',
        'ranges': {
            'canine': {'min': 2.00, 'max': 8.00},
            'feline': {'min': 2.00, 'max': 8.00}
        }
    },
    'fSAA': {
        'name': 'Amiloide A Sérico Felino',
        'unit': 'mg/L',
        'ranges': {
            'canine': None,
            'feline': {'min': 0.0, 'max': 5.0}
        }
    },
    'cPL': {
        'name': 'Lipasa Pancreática Canina',
        'unit': 'µg/L',
        'ranges': {
            'canine': {'min': 9.10, 'max': 19.40},
            'feline': {'min': 9.10, 'max': 19.40}
        }
    },
    'fPL': {
        'name': 'Lipasa Pancreática Felina',
        'unit': 'µg/L',
        'ranges': {
            'canine': None,
            'feline': {'min': 0.0, 'max': 3.5}
        }
    },
    'cT4': {
        'name': 'Tiroxina Canina',
        'unit': 'µg/dL',
        'ranges': {
            'canine': {'min': 1.0, 'max': 4.0},
            'feline': None
        }
    },
    'fT4': {
        'name': 'Tiroxina Felina',
        'unit': 'µg/dL',
        'ranges': {
            'canine': None,
            'feline': {'min': 1.2, 'max': 4.0}
        }
    },
    'cProg': {
        'name': 'Progesterona Canina',
        'unit': 'ng/mL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 1.0}, # < 1.0 (Anestro)
            'feline': None
        }
    },
    'cNT-proBNP': {
        'name': 'Péptido Natriurético Cerebral (Canino)',
        'unit': 'pmol/L',
        'ranges': {
            'canine': {'min': 0.0, 'max': 900.0},
            'feline': None
        }
    },
    'fNT-proBNP': {
        'name': 'Péptido Natriurético Cerebral (Felino)',
        'unit': 'pmol/L',
        'ranges': {
            'canine': None,
            'feline': {'min': 0.0, 'max': 100.0}
        }
    },

    # --- URINE MORPHOLOGY ---
    'URBC#': { # Renamed to avoid collision with blood RBC# (though blood is RBC)
        'name': 'Glóbulos Rojos en Orina',
        'unit': 'cél/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 5.0},
            'feline': {'min': 0.0, 'max': 5.0}
        }
    },
    'UWBC#': {
        'name': 'Leucocitos en Orina',
        'unit': 'cél/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 5.0},
            'feline': {'min': 0.0, 'max': 5.0}
        }
    },
    'RTE#': {
        'name': 'Células Epiteliales Renales',
        'unit': 'cél/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0}, # Ausente
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'SEC#': {
        'name': 'Células Escamosas',
        'unit': 'cél/µL',
        'ranges': {
            'canine': None, # Variable
            'feline': None
        }
    },
    'TEC#': {
        'name': 'Células Transicionales',
        'unit': 'cél/µL',
        'ranges': {
            'canine': None, # Raro/Ocasional
            'feline': None
        }
    },
    'UBAC#': {
        'name': 'Bacterias Generales en Orina',
        'unit': 'bac/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0}, # Ausente (Negativo)
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'UCOS#': {
        'name': 'Bacterias Formadoras de Cocos en Orina',
        'unit': 'bac/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'YEA#': {
        'name': 'Levaduras y Hongos en Orina',
        'unit': 'cél/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'FAT#': {
        'name': 'Cuerpos Lipídicos/Grasa en Orina',
        'unit': 'cél/µL',
        'ranges': {
            'canine': None,
            'feline': None # Variable en gatos
        }
    },
    'PHL#': {
        'name': 'Células Sanguíneas Alteradas en Orina',
        'unit': 'cél/µL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },

    # --- URINE CRYSTALS & CASTS ---
    'MAP#': {
        'name': 'Estruvita (Fosfato Amónico Magnésico)',
        'unit': '',
        'ranges': {
            'canine': None, # Raro / Moderado
            'feline': None
        }
    },
    'COMC#': {
        'name': 'Oxalato de Calcio Monohidratado',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'COD#': {
        'name': 'Oxalato de Calcio Dihidratado',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.00, 'max': 66.00}, # Bajo
            'feline': {'min': 0.00, 'max': 66.00}
        }
    },
    'CP#': {
        'name': 'Fosfato de Calcio',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'AUC#': {
        'name': 'Urato de Amonio',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'CYSC#': {
        'name': 'Cistina',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'CC#': {
        'name': 'Carbonato de Calcio',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'UBilC#': {
        'name': 'Bilirrubina en Orina',
        'unit': '',
        'ranges': {
            'canine': None, # Raro (Perro)
            'feline': {'min': 0.0, 'max': 0.0} # Ausente (Gato)
        }
    },
    'HYA#': {
        'name': 'Cilindros Hialinos',
        'unit': '',
        'ranges': {
            'canine': None, # Raro (<2 / campo)
            'feline': None
        }
    },
    'GRA#': {
        'name': 'Cilindros Granulosos',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'WAC#': {
        'name': 'Cilindros Leucocitarios',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'URBC-C#': {
        'name': 'Cilindros Eritrocíticos',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'RTC#': {
        'name': 'Cilindros Celulares/Renales',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },

    # --- FECAL ---
    'ANE#': {
        'name': 'Huevos de Nematodos/Áscaris',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0}, # Negativo
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'ALE#': {
        'name': 'Huevos de Anquilostomas',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'TRE#': {
        'name': 'Huevos de Trichuris',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'DIP#': {
        'name': 'Huevos de Cestodos',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'SPI#': {
        'name': 'Huevos de Espirúridos',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'TtE': {
        'name': 'Huevos de Tenia',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'FTg#': {
        'name': 'Giardia spp. (Fecal)',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'FCOD#': {
        'name': 'Coccidias (Fecal)',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'FCAM#': {
        'name': 'Bacterias Campylobacter-like (Fecal)',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'BACI#': {
        'name': 'Flora Bacteriana Anormal (Bacilos)',
        'unit': '',
        'ranges': {
            'canine': None,
            'feline': None
        }
    },
    'FYEA#': {
        'name': 'Esporas y Hongos (Fecal)',
        'unit': '',
        'ranges': {
            'canine': None, # Negativo/Bajo
            'feline': None
        }
    },
    'FWBC#': {
        'name': 'Células de Inflamación (Fecal)',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'FRBC#': {
        'name': 'Sangre Oculta/Glóbulos Rojos (Fecal)',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'LFAT#': {
        'name': 'Grasa Fecal',
        'unit': '',
        'ranges': {
            'canine': None, # Negativo/Bajo
            'feline': None
        }
    },
    'STA#': {
        'name': 'Almidón no Digerido (Fecal)',
        'unit': '',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.0},
            'feline': {'min': 0.0, 'max': 0.0}
        }
    },
    'FAF#': {
        'name': 'Fibras Musculares / Plantares (Fecal)',
        'unit': '',
        'ranges': {
            'canine': None, # Variable
            'feline': None
        }
    },

    # --- CHEMISTRY (ENZYMES) ---
    'ALP': {
        'name': 'Fosfatasa Alcalina',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 20.0, 'max': 150.0},
            'feline': {'min': 10.0, 'max': 80.0}
        }
    },
    'ALT': {
        'name': 'Alanina Aminotransferasa',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 10.0, 'max': 100.0},
            'feline': {'min': 10.0, 'max': 100.0}
        }
    },
    'AST': {
        'name': 'Aspartato Aminotransferasa',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 10.0, 'max': 50.0},
            'feline': {'min': 10.0, 'max': 50.0}
        }
    },
    'GGT': {
        'name': 'Gamma-Glutamil Transferasa',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 0.0, 'max': 10.0},
            'feline': {'min': 0.0, 'max': 10.0}
        }
    },
    'CPK': {
        'name': 'Creatina Quinasa',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 50.0, 'max': 200.0},
            'feline': {'min': 50.0, 'max': 250.0}
        }
    },
    'v-LIP': {
        'name': 'Lipasa Veterinaria',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 200.0, 'max': 800.0},
            'feline': {'min': 100.0, 'max': 600.0}
        }
    },
    'v-AMY': {
        'name': 'Amilasa Veterinaria',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 400.0, 'max': 1500.0},
            'feline': {'min': 500.0, 'max': 1500.0}
        }
    },
    'LDH': {
        'name': 'Deshidrogenasa Láctica',
        'unit': 'U/L',
        'ranges': {
            'canine': {'min': 0.0, 'max': 200.0},
            'feline': {'min': 0.0, 'max': 200.0}
        }
    },

    # --- METABOLIC / RENAL ---
    'BUN': {
        'name': 'Nitrógeno Ureico',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 15.0, 'max': 35.0},
            'feline': {'min': 15.0, 'max': 35.0}
        }
    },
    'CRE': {
        'name': 'Creatinina',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 0.6, 'max': 1.6},
            'feline': {'min': 0.8, 'max': 2.0}
        }
    },
    'GLU': {
        'name': 'Glucosa',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 70.0, 'max': 110.0},
            'feline': {'min': 70.0, 'max': 150.0}
        }
    },
    'IP': {
        'name': 'Fósforo Inorgánico',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 2.5, 'max': 6.0},
            'feline': {'min': 3.0, 'max': 6.5}
        }
    },
    'Ca': {
        'name': 'Calcio Total',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 9.0, 'max': 11.5},
            'feline': {'min': 8.5, 'max': 10.5}
        }
    },
    'TP': {
        'name': 'Proteína Total',
        'unit': 'g/dL',
        'ranges': {
            'canine': {'min': 5.5, 'max': 7.5},
            'feline': {'min': 6.0, 'max': 8.0}
        }
    },
    'ALB': {
        'name': 'Albúmina',
        'unit': 'g/dL',
        'ranges': {
            'canine': {'min': 2.5, 'max': 4.0},
            'feline': {'min': 2.5, 'max': 4.0}
        }
    },
    'TCHO': {
        'name': 'Colesterol Total',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 130.0, 'max': 300.0},
            'feline': {'min': 80.0, 'max': 220.0}
        }
    },
    'TG': {
        'name': 'Triglicéridos',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 20.0, 'max': 110.0},
            'feline': {'min': 20.0, 'max': 110.0}
        }
    },
    'TBIL': {
        'name': 'Bilirrubina Total',
        'unit': 'mg/dL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 0.5},
            'feline': {'min': 0.0, 'max': 0.5}
        }
    },
    'NH3': {
        'name': 'Amoníaco',
        'unit': 'µg/dL',
        'ranges': {
            'canine': {'min': 0.0, 'max': 100.0},
            'feline': {'min': 0.0, 'max': 100.0}
        }
    },

    # --- ELECTROLYTES ---
    'Na': {
        'name': 'Sodio',
        'unit': 'mEq/L',
        'ranges': {
            'canine': {'min': 140.0, 'max': 155.0},
            'feline': {'min': 145.0, 'max': 155.0}
        }
    },
    'K': {
        'name': 'Potasio',
        'unit': 'mEq/L',
        'ranges': {
            'canine': {'min': 3.5, 'max': 5.5},
            'feline': {'min': 3.5, 'max': 5.5}
        }
    },
    'Cl': {
        'name': 'Cloruro',
        'unit': 'mEq/L',
        'ranges': {
            'canine': {'min': 105.0, 'max': 115.0},
            'feline': {'min': 115.0, 'max': 125.0}
        }
    },
}

# Mapping of alternative abbreviations to standard keys
STANDARDS_MAPPING: Dict[str, str] = {
    # Red Series
    'RBC#': 'RBC',
    'HGB#': 'HGB',
    'HCT#': 'HCT',
    
    # White Series
    'LIN#': 'LYMP#',
    'LIN%': 'LYMP%',
    'LYM#': 'LYMP#',
    'LyM#': 'LYMP#',
    'LYM%': 'LYMP%',
    'NHG#': 'NSH#', 
    'NHG/WBC%': 'NSH/WBC%',
    'NHG/NEU%': 'NSH/NEU%',
    'BASH': 'BAS#',
    
    # Platelets
    'PLT-AGG': 'APLT#',
    
    # Chemistry
    'GOT': 'AST',
    'GPT': 'ALT',
    'T-CHO': 'TCHO',
    'T-BIL': 'TBIL',
    
    # Fecal
    'TXE#': 'ANE#',
    'GIA#': 'FTg#',
    'FLA#': 'FTg#',
    'TG#': 'FTg#',
    'To#': 'FTg#',
    'TTE#': 'TtE',
    'TtE#': 'TtE',
    'COD#': 'FCOD#',
    'COD0#': 'FCOD#',
    'COD1#': 'FCOD#',
    'COD2#': 'FCOD#',
    'CODO0#': 'FCOD#',
    'coD1#': 'FCOD#',
    'TRI#': 'TRE#',
    'CAM#': 'FCAM#',
    'BAC#': 'BACI#',
    'YEA#': 'FYEA#',
    'SS1#': 'FYEA#',
    'SS2#': 'FYEA#',
    'WBC#': 'FWBC#',
    'EPC#': 'FAF#',
    'PLA#': 'FAF#',
    'AF#': 'FAF#',
}

# Mapping of standard keys to legacy HemogramData fields (Core model compatibility)
LEGACY_HEMOGRAM_MAPPING: Dict[str, str] = {
    'RBC': 'hematies',
    'HGB': 'hemoglobina',
    'HCT': 'hematocrito',
    'MCV': 'vcm',
    'MCH': 'hcm',
    'MCHC': 'chcm',
    'PLT': 'plaquetas',
    'WBC': 'leucocitos',
    'NEU#': 'neutrofilos_segmentados',
    'LYMP#': 'linfocitos',
    'MON#': 'monocitos',
    'EOS#': 'eosinofilos',
    'BAS#': 'basofilos',
}

# Set of known chemistry codes for validation
CHEMISTRY_CODES = {
    'ALP', 'ALT', 'AST', 'GGT', 'CPK', 'v-LIP', 'v-AMY', 'LDH', # Enzymes
    'BUN', 'CRE', 'GLU', 'IP', 'Ca', 'TP', 'ALB', 'TCHO', 'TG', 'TBIL', 'NH3', # Metabolic / Renal
    'Na', 'K', 'Cl' # Electrolytes
}