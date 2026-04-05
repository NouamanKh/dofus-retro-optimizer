const ITEMS = [
  // ARMES - Force
  { id: "w_force_1", name: "Faux de la Corruption", type: "weapon", level: 100, elements: { vitalite: 0, sagesse: 0, force: 25, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "w_force_2", name: "Dague d'Émeraude", type: "weapon", level: 80, elements: { vitalite: 0, sagesse: 0, force: 20, intelligence: 0, chance: 10, agilite: 0 }, set: null },
  { id: "w_force_3", name: "Kam Kitsoune", type: "weapon", level: 150, elements: { vitalite: 0, sagesse: 0, force: 35, intelligence: 0, chance: 0, agilite: 5 }, set: "Kitsoune" },
  { id: "w_force_4", name: "Épée du Jugement", type: "weapon", level: 120, elements: { vitalite: 0, sagesse: 0, force: 28, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "w_force_5", name: "Marteau de Brokle Bworker", type: "weapon", level: 180, elements: { vitalite: 0, sagesse: 15, force: 40, intelligence: 0, chance: 0, agilite: 0 }, set: "Bworker" },
  { id: "w_force_6", name: "Marteau Lunaire", type: "weapon", level: 90, elements: { vitalite: 0, sagesse: 0, force: 22, intelligence: 5, chance: 0, agilite: 0 }, set: null },
  { id: "w_force_7", name: "Corne Démoniaque", type: "weapon", level: 110, elements: { vitalite: 0, sagesse: 0, force: 30, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "w_force_8", name: "Hache des Épaulettes de Flamme", type: "weapon", level: 70, elements: { vitalite: 0, sagesse: 0, force: 18, intelligence: 0, chance: 5, agilite: 0 }, set: null },

  // ARMES - Intelligence
  { id: "w_intelligence_1", name: "Fragment de Glace", type: "weapon", level: 95, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 28, chance: 0, agilite: 0 }, set: null },
  { id: "w_intelligence_2", name: "Marteau Tofu", type: "weapon", level: 50, elements: { vitalite: 0, sagesse: 0, force: 5, intelligence: 15, chance: 0, agilite: 0 }, set: null },
  { id: "w_intelligence_3", name: "Épée Sacrifiée", type: "weapon", level: 130, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 32, chance: 5, agilite: 0 }, set: null },
  { id: "w_intelligence_4", name: "Dague Vaporisation", type: "weapon", level: 85, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 22, chance: 0, agilite: 8 }, set: null },
  { id: "w_intelligence_5", name: "Marteau Tofu Royal", type: "weapon", level: 160, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 38, chance: 10, agilite: 0 }, set: "Tofu Royal" },
  { id: "w_intelligence_6", name: "Lame Hirondelle", type: "weapon", level: 105, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 25, chance: 0, agilite: 0 }, set: null },
  { id: "w_intelligence_7", name: "Baguette des Phasmae", type: "weapon", level: 75, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 20, chance: 0, agilite: 0 }, set: null },

  // ARMES - Sagesse
  { id: "w_sagesse_1", name: "Marteau de Groltle", type: "weapon", level: 140, elements: { vitalite: 0, sagesse: 35, force: 0, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "w_sagesse_2", name: "Marteau Feuille Errante", type: "weapon", level: 110, elements: { vitalite: 0, sagesse: 28, force: 0, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "w_sagesse_3", name: "Ancre des Âmes", type: "weapon", level: 125, elements: { vitalite: 0, sagesse: 30, force: 5, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "w_sagesse_4", name: "Lame de la Tombe", type: "weapon", level: 88, elements: { vitalite: 0, sagesse: 0, force: 5, intelligence: 0, chance: 0, agilite: 22 }, set: null },
  { id: "w_sagesse_5", name: "Marteau de Bois Poli", type: "weapon", level: 60, elements: { vitalite: 0, sagesse: 16, force: 0, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "w_sagesse_6", name: "Baguette Prespic", type: "weapon", level: 45, elements: { vitalite: 0, sagesse: 12, force: 0, intelligence: 5, chance: 0, agilite: 0 }, set: null },

  // ARMES - Agilité
  { id: "w_agilite_1", name: "Ailes de Brume", type: "weapon", level: 115, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 30 }, set: null },
  { id: "w_agilite_2", name: "Hache Zoth Zoth", type: "weapon", level: 100, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 25 }, set: null },
  { id: "w_agilite_3", name: "Dagues des Demos", type: "weapon", level: 135, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 35 }, set: null },
  { id: "w_agilite_4", name: "Fouet des Bloopers", type: "weapon", level: 78, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 8, chance: 0, agilite: 18 }, set: null },
  { id: "w_agilite_5", name: "Arc Lâche", type: "weapon", level: 55, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 15 }, set: null },
  { id: "w_agilite_6", name: "Hache Sak L Lombard", type: "weapon", level: 165, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 40 }, set: "Sak L Lombard" },

  // ARMES - Chance
  { id: "w_chance_1", name: "Canne du Cryptographe", type: "weapon", level: 118, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 30, agilite: 0 }, set: null },
  { id: "w_chance_2", name: "Kralove Royal", type: "weapon", level: 145, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 35, agilite: 0 }, set: "Kralove Royal" },
  { id: "w_chance_3", name: "Épée Dragonique", type: "weapon", level: 175, elements: { vitalite: 0, sagesse: 0, force: 10, intelligence: 0, chance: 40, agilite: 0 }, set: null },
  { id: "w_chance_4", name: "Dague Darklygmist", type: "weapon", level: 92, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 22, agilite: 0 }, set: null },
  { id: "w_chance_5", name: "Claymore des Épaulettes", type: "weapon", level: 65, elements: { vitalite: 0, sagesse: 0, force: 5, intelligence: 0, chance: 18, agilite: 0 }, set: null },

  // CHAPEAUX - Force
  { id: "h_force_1", name: "Casque Kannibul", type: "hat", level: 80, elements: { vitalite: 0, sagesse: 5, force: 0, intelligence: 15, chance: 0, agilite: 0 }, set: null },
  { id: "h_force_2", name: "Coiffe Drheller", type: "hat", level: 95, elements: { vitalite: 0, sagesse: 0, force: 22, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "h_force_3", name: "Coiffe Bworker", type: "hat", level: 180, elements: { vitalite: 0, sagesse: 12, force: 38, intelligence: 0, chance: 0, agilite: 0 }, set: "Bworker" },
  { id: "h_force_4", name: "Coiffe Cuir Tanée", type: "hat", level: 55, elements: { vitalite: 0, sagesse: 0, force: 14, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "h_force_5", name: "Casque Crapaud Infernal", type: "hat", level: 140, elements: { vitalite: 0, sagesse: 0, force: 32, intelligence: 0, chance: 5, agilite: 0 }, set: null },

  // CHAPEAUX - Intelligence
  { id: "h_intelligence_1", name: "Chapeau Tofu", type: "hat", level: 50, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 15, chance: 5, agilite: 0 }, set: null },
  { id: "h_intelligence_2", name: "Chapeau Tofu Royal", type: "hat", level: 160, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 35, chance: 8, agilite: 0 }, set: "Tofu Royal" },
  { id: "h_intelligence_3", name: "Capuche des Phasmae", type: "hat", level: 72, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 18, chance: 0, agilite: 0 }, set: null },
  { id: "h_intelligence_4", name: "Masque Wak Wak Enneigé", type: "hat", level: 120, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 28, chance: 5, agilite: 0 }, set: null },
  { id: "h_intelligence_5", name: "Chapeau Feuille Errante", type: "hat", level: 105, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 25, chance: 5, agilite: 0 }, set: null },

  // CHAPEAUX - Sagesse
  { id: "h_sagesse_1", name: "Oreilles Prespic", type: "hat", level: 45, elements: { vitalite: 0, sagesse: 12, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "h_sagesse_2", name: "Tête Treechnid", type: "hat", level: 130, elements: { vitalite: 0, sagesse: 30, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "h_sagesse_3", name: "Coiffe Groltle", type: "hat", level: 140, elements: { vitalite: 0, sagesse: 35, force: 0, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "h_sagesse_4", name: "Cornes Minotoror", type: "hat", level: 155, elements: { vitalite: 0, sagesse: 32, force: 8, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "h_sagesse_5", name: "Masque de Chêne", type: "hat", level: 60, elements: { vitalite: 0, sagesse: 16, force: 0, intelligence: 0, chance: 0, agilite: 0 }, set: null },

  // CHAPEAUX - Agilité
  { id: "h_agilite_1", name: "Casque Bottes Ailées", type: "hat", level: 110, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 26 }, set: null },
  { id: "h_agilite_2", name: "Masque Kitsoune", type: "hat", level: 150, elements: { vitalite: 0, sagesse: 0, force: 8, intelligence: 0, chance: 0, agilite: 35 }, set: "Kitsoune" },
  { id: "h_agilite_3", name: "Tête Sak L Lombard", type: "hat", level: 165, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 40 }, set: "Sak L Lombard" },
  { id: "h_agilite_4", name: "Chapeau Blooper", type: "hat", level: 78, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 18 }, set: null },
  { id: "h_agilite_5", name: "Tête Krakusk", type: "hat", level: 100, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 24 }, set: null },

  // CHAPEAUX - Chance
  { id: "h_chance_1", name: "Casque Kralove Royal", type: "hat", level: 145, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 35, agilite: 0 }, set: "Kralove Royal" },
  { id: "h_chance_2", name: "Tête Crocoburio", type: "hat", level: 125, elements: { vitalite: 0, sagesse: 0, force: 8, intelligence: 0, chance: 28, agilite: 0 }, set: null },
  { id: "h_chance_3", name: "Vlad Sombre", type: "hat", level: 170, elements: { vitalite: 0, sagesse: 0, force: 5, intelligence: 0, chance: 38, agilite: 5 }, set: null },
  { id: "h_chance_4", name: "Chapeau Lunaire", type: "hat", level: 88, elements: { vitalite: 0, sagesse: 15, force: 5, intelligence: 5, chance: 15, agilite: 5 }, set: null },
  { id: "h_chance_5", name: "Masque de la Tombe", type: "hat", level: 115, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 26, agilite: 0 }, set: null },

  // CAPES - Force
  { id: "c_force_1", name: "Cape Drheller", type: "cloak", level: 95, elements: { vitalite: 0, sagesse: 0, force: 22, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "c_force_2", name: "Cape Bworker", type: "cloak", level: 180, elements: { vitalite: 0, sagesse: 8, force: 40, intelligence: 0, chance: 0, agilite: 0 }, set: "Bworker" },
  { id: "c_force_3", name: "Cape Infernale", type: "cloak", level: 135, elements: { vitalite: 0, sagesse: 0, force: 30, intelligence: 0, chance: 5, agilite: 0 }, set: null },
  { id: "c_force_4", name: "Cape Salamandre", type: "cloak", level: 70, elements: { vitalite: 0, sagesse: 0, force: 16, intelligence: 0, chance: 0, agilite: 0 }, set: null },

  // CAPES - Intelligence
  { id: "c_intelligence_1", name: "Cape des Phasmae", type: "cloak", level: 72, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 18, chance: 0, agilite: 0 }, set: null },
  { id: "c_intelligence_2", name: "Cape Tofu Royal", type: "cloak", level: 160, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 35, chance: 5, agilite: 0 }, set: "Tofu Royal" },
  { id: "c_intelligence_3", name: "Cape de Glace", type: "cloak", level: 90, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 22, chance: 0, agilite: 5 }, set: null },
  { id: "c_intelligence_4", name: "Cape de Gourde", type: "cloak", level: 55, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 14, chance: 0, agilite: 0 }, set: null },

  // CAPES - Sagesse
  { id: "c_sagesse_1", name: "Cape Groltle", type: "cloak", level: 140, elements: { vitalite: 0, sagesse: 32, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "c_sagesse_2", name: "Cape Minotoror", type: "cloak", level: 155, elements: { vitalite: 0, sagesse: 35, force: 5, intelligence: 0, chance: 0, agilite: 0 }, set: null },
  { id: "c_sagesse_3", name: "Cape Feuille Errante", type: "cloak", level: 105, elements: { vitalite: 0, sagesse: 25, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "c_sagesse_4", name: "Cape Treechnid", type: "cloak", level: 130, elements: { vitalite: 0, sagesse: 28, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },

  // CAPES - Agilité
  { id: "c_agilite_1", name: "Cape Bottes Ailées", type: "cloak", level: 110, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 26 }, set: null },
  { id: "c_agilite_2", name: "Cape Kitsoune", type: "cloak", level: 150, elements: { vitalite: 0, sagesse: 0, force: 5, intelligence: 0, chance: 0, agilite: 35 }, set: "Kitsoune" },
  { id: "c_agilite_3", name: "Cape Blooper", type: "cloak", level: 78, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 5, agilite: 18 }, set: null },
  { id: "c_agilite_4", name: "Cape Sak L Lombard", type: "cloak", level: 165, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 0, agilite: 40 }, set: "Sak L Lombard" },

  // CAPES - Chance
  { id: "c_chance_1", name: "Cape Kralove Royal", type: "cloak", level: 145, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 35, agilite: 0 }, set: "Kralove Royal" },
  { id: "c_chance_2", name: "Cape Vlad Sombre", type: "cloak", level: 170, elements: { vitalite: 0, sagesse: 0, force: 5, intelligence: 0, chance: 38, agilite: 5 }, set: null },
  { id: "c_chance_3", name: "Cape de la Tombe", type: "cloak", level: 115, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 26, agilite: 0 }, set: null },
  { id: "c_chance_4", name: "Cape Crocoburio", type: "cloak", level: 125, elements: { vitalite: 0, sagesse: 0, force: 8, intelligence: 0, chance: 28, agilite: 0 }, set: null },

  // AMULETTES
  { id: "amu_1", name: "Pendentif de Fureur Élémentaire", type: "amulet", level: 100, elements: { vitalite: 0, sagesse: 20, force: 20, intelligence: 20, chance: 20, agilite: 20 }, set: null },
  { id: "amu_2", name: "Amulette de Puissance Force", type: "amulet", level: 85, elements: { vitalite: 0, sagesse: 0, force: 25, intelligence: 0, chance: 5, agilite: 0 }, set: null },
  { id: "amu_3", name: "Amulette de Puissance Intelligence", type: "amulet", level: 85, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 25, chance: 5, agilite: 0 }, set: null },
  { id: "amu_4", name: "Amulette de Puissance Sagesse", type: "amulet", level: 85, elements: { vitalite: 0, sagesse: 25, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "amu_5", name: "Amulette de Puissance Agilité", type: "amulet", level: 85, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 25 }, set: null },
  { id: "amu_6", name: "Amulette de Puissance Chance", type: "amulet", level: 85, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 30, agilite: 0 }, set: null },
  { id: "amu_7", name: "Amulette Kannibul", type: "amulet", level: 80, elements: { vitalite: 0, sagesse: 5, force: 0, intelligence: 15, chance: 0, agilite: 0 }, set: null },
  { id: "amu_8", name: "Collier Dreggon", type: "amulet", level: 150, elements: { vitalite: 0, sagesse: 0, force: 30, intelligence: 0, chance: 5, agilite: 0 }, set: null },
  { id: "amu_9", name: "Amulette d'Ougal脖", type: "amulet", level: 180, elements: { vitalite: 15, sagesse: 15, force: 15, intelligence: 15, chance: 15, agilite: 15 }, set: null },

  // ANNEAUX
  { id: "ring_1", name: "Anneau de Puissance Force", type: "ring", level: 75, elements: { vitalite: 0, sagesse: 0, force: 15, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "ring_2", name: "Anneau de Puissance Intelligence", type: "ring", level: 75, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 15, chance: 0, agilite: 5 }, set: null },
  { id: "ring_3", name: "Anneau de Puissance Sagesse", type: "ring", level: 75, elements: { vitalite: 0, sagesse: 15, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "ring_4", name: "Anneau de Puissance Agilité", type: "ring", level: 75, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 15 }, set: null },
  { id: "ring_5", name: "Anneau de Puissance Chance", type: "ring", level: 75, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 18, agilite: 0 }, set: null },
  { id: "ring_6", name: "Anneau du Cryptographe", type: "ring", level: 95, elements: { vitalite: 8, sagesse: 8, force: 8, intelligence: 8, chance: 8, agilite: 8 }, set: null },
  { id: "ring_7", name: "Anneau Kannibul", type: "ring", level: 80, elements: { vitalite: 0, sagesse: 5, force: 0, intelligence: 10, chance: 0, agilite: 0 }, set: null },
  { id: "ring_8", name: "Anneau Tofu Royal", type: "ring", level: 160, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 22, chance: 5, agilite: 0 }, set: "Tofu Royal" },
  { id: "ring_9", name: "Anneau Bworker", type: "ring", level: 180, elements: { vitalite: 0, sagesse: 5, force: 25, intelligence: 0, chance: 0, agilite: 0 }, set: "Bworker" },
  { id: "ring_10", name: "Anneau Sak L Lombard", type: "ring", level: 165, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 25 }, set: "Sak L Lombard" },

  // CEINTURES
  { id: "belt_1", name: "Ceinture Force du Djaul", type: "belt", level: 90, elements: { vitalite: 0, sagesse: 0, force: 20, intelligence: 0, chance: 5, agilite: 0 }, set: null },
  { id: "belt_2", name: "Ceinture Intelligence du Djaul", type: "belt", level: 90, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 20, chance: 5, agilite: 0 }, set: null },
  { id: "belt_3", name: "Ceinture Sagesse du Djaul", type: "belt", level: 90, elements: { vitalite: 0, sagesse: 20, force: 0, intelligence: 0, chance: 5, agilite: 0 }, set: null },
  { id: "belt_4", name: "Ceinture Agilité du Djaul", type: "belt", level: 90, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 20 }, set: null },
  { id: "belt_5", name: "Ceinture Chance du Djaul", type: "belt", level: 90, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 25, agilite: 0 }, set: null },
  { id: "belt_6", name: "Ceinture Kitsoune", type: "belt", level: 150, elements: { vitalite: 0, sagesse: 0, force: 15, intelligence: 0, chance: 0, agilite: 20 }, set: "Kitsoune" },
  { id: "belt_7", name: "Ceinture Kralove Royal", type: "belt", level: 145, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 25, agilite: 0 }, set: "Kralove Royal" },
  { id: "belt_8", name: "Ceinture Groltle", type: "belt", level: 140, elements: { vitalite: 0, sagesse: 22, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "belt_9", name: "Ceinture Sak L Lombard", type: "belt", level: 165, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 25 }, set: "Sak L Lombard" },

  // BOTTES
  { id: "boot_1", name: "Bottes Tofu Force", type: "boots", level: 65, elements: { vitalite: 0, sagesse: 0, force: 15, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "boot_2", name: "Bottes Tofu Intelligence", type: "boots", level: 65, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 15, chance: 0, agilite: 5 }, set: null },
  { id: "boot_3", name: "Bottes Tofu Sagesse", type: "boots", level: 65, elements: { vitalite: 0, sagesse: 15, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "boot_4", name: "Bottes Tofu Agilité", type: "boots", level: 65, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 15 }, set: null },
  { id: "boot_5", name: "Bottes Tofu Chance", type: "boots", level: 65, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 18, agilite: 0 }, set: null },
  { id: "boot_6", name: "Bottes Ailées", type: "boots", level: 110, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 8, agilite: 22 }, set: null },
  { id: "boot_7", name: "Bottes Kannibul", type: "boots", level: 80, elements: { vitalite: 0, sagesse: 5, force: 0, intelligence: 10, chance: 0, agilite: 0 }, set: null },
  { id: "boot_8", name: "Bottes Blooper", type: "boots", level: 78, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 8, chance: 0, agilite: 15 }, set: null },
  { id: "boot_9", name: "Bottes Tofu Royal", type: "boots", level: 160, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 25, chance: 5, agilite: 5 }, set: "Tofu Royal" },
  { id: "boot_10", name: "Bottes Bworker", type: "boots", level: 180, elements: { vitalite: 0, sagesse: 8, force: 28, intelligence: 0, chance: 0, agilite: 0 }, set: "Bworker" },
  { id: "boot_11", name: "Bottes Kitsoune", type: "boots", level: 150, elements: { vitalite: 0, sagesse: 0, force: 12, intelligence: 0, chance: 0, agilite: 25 }, set: "Kitsoune" },
  { id: "boot_12", name: "Bottes Sak L Lombard", type: "boots", level: 165, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 5, agilite: 30 }, set: "Sak L Lombard" },

  // BOCLIERS
  { id: "sh_1", name: "Bouclier Force du Héros", type: "shield", level: 70, elements: { vitalite: 0, sagesse: 0, force: 18, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "sh_2", name: "Bouclier Intelligence du Héros", type: "shield", level: 70, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 18, chance: 0, agilite: 5 }, set: null },
  { id: "sh_3", name: "Bouclier Sagesse du Héros", type: "shield", level: 70, elements: { vitalite: 0, sagesse: 18, force: 0, intelligence: 0, chance: 0, agilite: 5 }, set: null },
  { id: "sh_4", name: "Bouclier Agilité du Héros", type: "shield", level: 70, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 5, chance: 0, agilite: 18 }, set: null },
  { id: "sh_5", name: "Bouclier Chance du Héros", type: "shield", level: 70, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 0, chance: 22, agilite: 0 }, set: null },
  { id: "sh_6", name: "Bouclier Kannibul", type: "shield", level: 80, elements: { vitalite: 0, sagesse: 5, force: 0, intelligence: 12, chance: 0, agilite: 0 }, set: null },
  { id: "sh_7", name: "Bouclier Tofu Royal", type: "shield", level: 160, elements: { vitalite: 0, sagesse: 0, force: 0, intelligence: 28, chance: 5, agilite: 0 }, set: "Tofu Royal" },
  { id: "sh_8", name: "Bouclier Bworker", type: "shield", level: 180, elements: { vitalite: 0, sagesse: 8, force: 32, intelligence: 0, chance: 0, agilite: 0 }, set: "Bworker" },
];
