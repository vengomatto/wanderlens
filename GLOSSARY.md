# Wanderlens

A personal travel-recommendation app that learns a user's taste from their photo
archive and suggests new destinations. Single-user today, designed to become a
portable open-source app later.

## Language

**Photo Archive**:
The body of photos a user owns, from which taste is inferred.
_Avoid_: library, image set, collection

**Photo Source**:
An origin the app can read a Photo Archive from (e.g. a local folder or a photo
manager). Multiple Photo Sources may back one Photo Archive.
_Avoid_: backend, connector, mount

**Preference Factor**:
One dimension of a user's travel taste. v1 factors: visited geography, visual
aesthetics, and subjects/activities.
_Avoid_: signal, feature, criterion

**Taste Profile**:
The learned model of a user's travel taste, assembled from their Photo Archive
across the Preference Factors.
_Avoid_: user model, persona, preference set

**Destination**:
A **self-contained travel area** the app can recommend (a region or coherent
area such as *Costa del Sol* or *Cinque Terre*), not a single municipality or a
stop within a region. Distinct from a place the user has visited.
_Avoid_: location, spot, POI, town, city

**Recommendation**:
A Destination proposed to the user, ranked against the Taste Profile and
carrying an explanation grounded in the user's own photos.
_Avoid_: suggestion, hit, result
