# levenshtein
def distance(s1, s2):
    if len(s1) < len(s2):
        return distance(s2, s1)

    # len(s1) >= len(s2)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1  # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1  # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def didyoumean(term, other_terms, number_of_hints):
    import collections
    nearest_terms = collections.OrderedDict(
        sorted({distance(term, s): s for s in [x for x in other_terms if x != term]}.items()))

    return list(nearest_terms.values())[0:number_of_hints]