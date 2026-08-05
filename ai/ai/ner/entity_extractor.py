"""
Named Entity Recognition for Map Synchronization in Arkana
Extracts tribe names, locations, and time periods from generated responses
to emit map events via SSE.
"""

import spacy
import re
import asyncio
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NERConfig:
    """Configuration for NER extractor"""
    spacy_model: str = "en_core_web_sm"
    tribe_lookup_path: Optional[str] = None  # Path to tribe name mapping file


class EntityExtractor:
    """
    Extracts entities from generated text for map synchronization.
    Emits structured events: MAP_HIGHLIGHT, MAP_PAN, TIMELINE_SEEK
    """
    
    # Tribe name to tribe_id mapping (expand as corpus grows)
    TRIBE_MAP = {
        "warli": "tribe_warli_001",
        "gond": "tribe_gond_001", 
        "bhil": "tribe_bhil_001",
        "santali": "tribe_santali_001",
        "muria": "tribe_muria_001",
        "baiga": "tribe_baiga_001",
        "madhubani": "region_bihar_001",
        "pithora": "tribe_pithora_001",
        "bhilala": "tribe_bhilala_001",
        "korku": "tribe_korku_001",
        "kol": "tribe_kol_001",
        "saharia": "tribe_saharia_001",
        "korku": "tribe_korku_001",
        "bharia": "tribe_bharia_001",
        "patelia": "tribe_patelia_001",
        "pawra": "tribe_pawra_001",
        "chamar": "tribe_chamar_001",
        "dhodia": "tribe_dhodia_001",
        "gamit": "tribe_gamit_001",
        "kathodi": "tribe_kathodi_001",
        "kokna": "tribe_kokna_001",
        "kolam": "tribe_kolam_001",
        "kondh": "tribe_kondh_001",
        "koya": "tribe_koya_001",
        "lambadi": "tribe_lambadi_001",
        "mali": "tribe_mali_001",
        "maratha": "tribe_maratha_001",
        "meena": "tribe_meena_001",
        "meitei": "tribe_meitei_001",
        "mishing": "tribe_mishing_001",
        "munda": "tribe_munda_001",
        "naga": "tribe_naga_001",
        "oron": "tribe_oron_001",
        "paliyan": "tribe_paliyan_001",
        "paniyan": "tribe_paniyan_001",
        "rabha": "tribe_rabha_001",
        "rabari": "tribe_rabari_001",
        "rathwa": "tribe_rathwa_001",
        "sahariya": "tribe_sahariya_001",
        "santhal": "tribe_santhal_001",
        "saora": "tribe_saora_001",
        "siddi": "tribe_siddi_001",
        "soliga": "tribe_soliga_001",
        "toda": "tribe_toda_001",
        "yarava": "tribe_yarava_001",
    }
    
    # Region name mappings
    REGION_MAP = {
        "maharashtra": "region_maharashtra_001",
        "madhya pradesh": "region_madhya_pradesh_001",
        "gujarat": "region_gujarat_001",
        "rajasthan": "region_rajasthan_001",
        "bihar": "region_bihar_001",
        "jharkhand": "region_jharkhand_001",
        "odisha": "region_odisha_001",
        "chhattisgarh": "region_chhattisgarh_001",
        "west bengal": "region_west_bengal_001",
        "andhra pradesh": "region_andhra_pradesh_001",
        "telangana": "region_telangana_001",
        "karnataka": "region_karnataka_001",
        "tamil nadu": "region_tamil_nadu_001",
        "kerala": "region_kerala_001",
        "uttar pradesh": "region_uttar_pradesh_001",
        "himachal pradesh": "region_himachal_pradesh_001",
        "uttarakhand": "region_uttarakhand_001",
        "assam": "region_assam_001",
        "manipur": "region_manipur_001",
        "meghalaya": "region_meghalaya_001",
        "mizoram": "region_mizoram_001",
        "nagaland": "region_nagaland_001",
        "tripura": "region_tripura_001",
        "arunachal pradesh": "region_arunachal_pradesh_001",
        "sikkim": "region_sikkim_001",
        "goa": "region_goa_001",
        "punjab": "region_punjab_001",
        "haryana": "region_haryana_001",
        "delhi": "region_delhi_001",
    }
    
    def __init__(self, config: Optional[NERConfig] = None):
        self.config = config or NERConfig()
        self.nlp = None
        self._load_model()
        
        # Load custom tribe lookup if provided
        if self.config.tribe_lookup_path:
            self._load_custom_tribe_map()
            
        self._compile_tribe_regexes()
        
    def _compile_tribe_regexes(self):
        """Compile word-boundary regexes for all tribes to prevent false positives"""
        self.compiled_tribes = {}
        for tribe_name, tribe_id in self.TRIBE_MAP.items():
            self.compiled_tribes[tribe_name] = (tribe_id, re.compile(rf"\b{re.escape(tribe_name)}\b", re.IGNORECASE))
    
    def _load_model(self):
        """Load spaCy model"""
        try:
            self.nlp = spacy.load(self.config.spacy_model)
            logger.info(f"Loaded spaCy model: {self.config.spacy_model}")
        except OSError:
            logger.warning(f"spaCy model {self.config.spacy_model} not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", self.config.spacy_model], check=True)
            self.nlp = spacy.load(self.config.spacy_model)
    
    def _load_custom_tribe_map(self):
        """Load custom tribe mappings from JSON file"""
        import json
        try:
            with open(self.config.tribe_lookup_path, 'r') as f:
                custom_map = json.load(f)
                self.TRIBE_MAP.update(custom_map)
            logger.info(f"Loaded custom tribe mappings from {self.config.tribe_lookup_path}")
        except Exception as e:
            logger.error(f"Failed to load custom tribe map: {e}")
    
    async def extract_map_events(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract map synchronization events from generated text.
        
        Returns:
            List of event dicts with types: MAP_HIGHLIGHT, MAP_PAN, TIMELINE_SEEK
        """
        events = []
        text_lower = text.lower()
        
        # 1. Tribe name detection (highest priority for map highlighting)
        tribe_events = self._extract_tribe_events(text_lower)
        events.extend(tribe_events)
        
        # 2. spaCy NER for locations (GPE) and dates
        doc = await asyncio.to_thread(self.nlp, text)
        ner_events = self._extract_ner_events(doc)
        events.extend(ner_events)
        
        # 3. Deduplicate events (same tribe/location mentioned multiple times)
        events = self._deduplicate_events(events)
        
        return events
    
    def _extract_tribe_events(self, text_lower: str) -> List[Dict[str, Any]]:
        """Extract tribe mentions from text"""
        events = []
        
        for tribe_name, (tribe_id, pattern) in self.compiled_tribes.items():
            if pattern.search(text_lower):
                events.append({
                    "type": "MAP_HIGHLIGHT",
                    "tribe_id": tribe_id,
                    "tribe_name": tribe_name.title()
                })
        
        return events
    
    def _extract_ner_events(self, doc) -> List[Dict[str, Any]]:
        """Extract events from spaCy NER"""
        events = []
        seen_locations = set()
        
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Geopolitical entity (country, city, state)
                loc_lower = ent.text.lower()
                if loc_lower not in seen_locations:
                    # Check if it's a known region
                    region_id = self.REGION_MAP.get(loc_lower)
                    events.append({
                        "type": "MAP_PAN",
                        "location": ent.text,
                        "region_id": region_id
                    })
                    seen_locations.add(loc_lower)
            
            elif ent.label_ == "DATE":
                # Extract years/periods for timeline
                if any(c.isdigit() for c in ent.text):
                    events.append({
                        "type": "TIMELINE_SEEK",
                        "period": ent.text
                    })
        
        return events
    
    def _deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events based on type and key identifier"""
        seen = set()
        deduped = []
        
        for event in events:
            # Create unique key based on event type and main identifier
            if event["type"] == "MAP_HIGHLIGHT":
                key = f"MAP_HIGHLIGHT:{event.get('tribe_id', '')}"
            elif event["type"] == "MAP_PAN":
                key = f"MAP_PAN:{event.get('location', '').lower()}"
            elif event["type"] == "TIMELINE_SEEK":
                key = f"TIMELINE_SEEK:{event.get('period', '')}"
            else:
                key = str(event)
            
            if key not in seen:
                seen.add(key)
                deduped.append(event)
        
        return deduped
    
    def add_tribe_mapping(self, tribe_name: str, tribe_id: str):
        """Add a new tribe mapping at runtime"""
        tribe_lower = tribe_name.lower()
        self.TRIBE_MAP[tribe_lower] = tribe_id
        self.compiled_tribes[tribe_lower] = (tribe_id, re.compile(rf"\b{re.escape(tribe_lower)}\b", re.IGNORECASE))
    
    def add_region_mapping(self, region_name: str, region_id: str):
        """Add a new region mapping at runtime"""
        self.REGION_MAP[region_name.lower()] = region_id


# Global instance for easy import
_extractor_instance = None

def get_extractor(config: Optional[NERConfig] = None) -> EntityExtractor:
    """Get or create global extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor(config)
    return _extractor_instance


async def extract_map_events(text: str) -> List[Dict[str, Any]]:
    """Convenience function to extract map events from text"""
    extractor = get_extractor()
    return await extractor.extract_map_events(text)


if __name__ == "__main__":
    # Test NER extraction
    config = NERConfig()
    extractor = EntityExtractor(config)
    
    test_responses = [
        "Warli painting uses circles for the sun and moon, triangles for mountains. The Warli tribe lives in Maharashtra.",
        "The Gond art of Madhya Pradesh features vibrant colors. The Gond tribe creates these paintings.",
        "In 1200 CE, the Mughal empire expanded into the Deccan region. Bhil art from Gujarat shows similar patterns.",
        "Madhubani painting originated in the Mithila region of Bihar around 2500 years ago.",
        "The malicious intent of the king was to conquer the okola forest."
    ]
    
    async def run_tests():
        for response in test_responses:
            print(f"\nText: {response}")
            events = await extractor.extract_map_events(response)
            print("Events:")
            for event in events:
                print(f"  {event}")
                
    asyncio.run(run_tests())