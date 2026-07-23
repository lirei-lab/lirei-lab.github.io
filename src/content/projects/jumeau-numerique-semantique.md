---
title:
  fr: "Jumeau numérique sémantique d'un bâtiment universitaire"
  en: "Semantic digital twin of a university building"
summary:
  fr: "Jumeau numérique du pavillon Tapan-K.-Bose de l'UQTR : données BACnet en direct, graphe de connaissances multi-ontologies et interrogation en langage naturel assistée par IA."
  en: "Digital twin of UQTR's Tapan K. Bose building: live BACnet data, a multi-ontology knowledge graph and AI-assisted natural-language querying."
description:
  fr: "Ce projet construit un jumeau numérique sémantique d'un bâtiment réel de l'UQTR. Les valeurs des points BACnet du bâtiment circulent en direct, via MQTT, vers un entrepôt de triplets RDF où elles sont décrites par quatre ontologies complémentaires du domaine du bâtiment : Brick, ASHRAE 223P, RealEstateCore et Haystack.\n\nLe graphe de connaissances est l'artefact central : il est validé par SHACL, interrogeable en SPARQL et exposé comme un service de questions-réponses en langage naturel appuyé par un grand modèle de langage (GraphRAG). Les priorités de conception sont, dans l'ordre : justesse sémantique, interopérabilité, simplicité opérationnelle et coût."
  en: "This project builds a semantic digital twin of a real UQTR building. Live BACnet point values stream through MQTT into an RDF triple store, where they are described with four complementary building-domain ontologies: Brick, ASHRAE 223P, RealEstateCore and Haystack.\n\nThe knowledge graph is the central artefact: it is validated with SHACL, queryable in SPARQL and exposed as a natural-language question-answering service backed by a large language model (GraphRAG). Design priorities are, in order: semantic correctness, interoperability, operational simplicity and cost."
axis: ml
status: active
partners: ["UQTR"]
image: /images/projects/building-graph.png
imageAlt:
  fr: "Graphe de connaissances du bâtiment (visualisation de nœuds et de liens)"
  en: "Building knowledge graph (nodes and links visualization)"
featured: true
---
