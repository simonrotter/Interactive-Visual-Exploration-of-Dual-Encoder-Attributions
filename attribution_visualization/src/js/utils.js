function filterAttributionsByValueRange(attributions, includeRange, excludeRange = null) {
  const selected = [];

  if (typeof attributions[0]?.[0] === 'number') {
    //2D array
    for (let i = 0; i < attributions.length; i++) {
      for (let j = 0; j < attributions[i].length; j++) {
        const value = attributions[i][j];
        const inInclude = value >= includeRange.left && value <= includeRange.right;
        const inExclude = excludeRange && value >= excludeRange.left && value <= excludeRange.right;

        if (inInclude && !inExclude) {
          selected.push([i, j]);
        }
      }
    }
  } else if (Array.isArray(attributions[0]?.[0])) {
    //3D array
    for (let i = 0; i < attributions.length; i++) {
      for (let j = 0; j < attributions[i].length; j++) {
        for (let k = 0; k < attributions[i][j].length; k++) {
          const value = attributions[i][j][k];
          const inInclude = value >= includeRange.left && value <= includeRange.right;
          const inExclude = excludeRange && value >= excludeRange.left && value <= excludeRange.right;

          if (inInclude && !inExclude) {
            selected.push([i, j, k]);
          }
        }
      }
    }
  }

  return selected;
}


function getIndexTuples(data) {
  if (!Array.isArray(data)) return []

  //2D
  if (typeof data[0]?.[0] === 'number') {
    return data.flatMap((row, i) =>
      row.map((_, j) => [i, j])
    )
  }

  //3D
  if (Array.isArray(data[0]?.[0])) {
    return data.flatMap((matrix, i) =>
      matrix.flatMap((row, j) =>
        row.map((_, k) => [i, j, k])
      )
    )
  }

  return []
}


  
export function getAttributionShare(attributions, includeRange = {left:-1,right:1}, excludeRange={left:0,right:0}){
    const selectedIndices = filterAttributionsByValueRange(attributions, includeRange, excludeRange);
    const totalIndices = getIndexTuples(attributions)

    const subsetScores = computeSimilarityScores(attributions, selectedIndices);
    const totalScores = computeSimilarityScores(attributions, totalIndices);

    return computeShare(subsetScores, totalScores);
}

//Compute similarity scores for the given psoitions in attributions
function computeSimilarityScores(attributions, indices) {
  let pos = 0, neg = 0, total = 0, signed = 0;

  indices.forEach((index) => {
    const value = index.length === 2
      ? attributions[index[0]][index[1]]    //2D
      : attributions[index[0]][index[1]][index[2]]; //3D

    if (value > 0) pos += value;
    else if (value < 0) neg += value;

    total += Math.abs(value);
    signed += value;
  });

  return { pos, neg, total, signed };
}

//compute masShare signEdShare and signedSum. signedShare has scaling factor so that maximum absoulute share is 1, for example to perfectly fill up the progressbar 
  function computeShare(subsetScores, totalScores) {    
    const maxGlobal = Math.max(totalScores.pos, Math.abs(totalScores.neg));
    const globalScale = maxGlobal !== 0 ? 1 / maxGlobal : 1;
    const scaledSignedShare = subsetScores.signed * globalScale;
    
    return {
      massShare: totalScores.total > 0 ? subsetScores.total / totalScores.total : 0,
      signedShare: scaledSignedShare,
      signedSum: totalScores.signed !== 0 ? (subsetScores.signed / totalScores.signed) * Math.abs(totalScores.signed) : 0
    };
  }
  

//removes eos/cls and attribs and categorization
export function deleteSpecialTokens(input) {
  const {
    tokens_a,
    tokens_b,
    attributions,
    tokens_a_categorized = [],
    tokens_b_categorized = [],
    ...extras
  } = input;

  
//edit copeies
  let filteredTokensA           = tokens_a.slice();
  let filteredTokensB           = tokens_b.slice();
  let filteredRows              = attributions.map(row => row.slice());
  let filteredCategA            = tokens_a_categorized.slice();
  let filteredCategB            = tokens_b_categorized.slice();

  if (filteredTokensA[0] === 'CLS' || filteredTokensA[0] === '[CLS]') {
    filteredTokensA.shift();
    filteredRows.shift();
    if (filteredCategA.length) {
      filteredCategA.shift();
    }
  }
  const lastA = filteredTokensA[filteredTokensA.length - 1];
  if (lastA === 'EOS' || lastA === '[EOS]') {
    filteredTokensA.pop();
    filteredRows.pop();
    if (filteredCategA.length) {
      filteredCategA.pop();
    }
  }

  if (filteredTokensB[0] === 'CLS' || filteredTokensB[0] === '[CLS]') {
    filteredTokensB.shift();
    filteredRows.forEach(row => row.shift());
    if (filteredCategB.length) {
      filteredCategB.shift();
    }
  }
  const lastB = filteredTokensB[filteredTokensB.length - 1];
  if (lastB === 'EOS' || lastB === '[EOS]') {
    filteredTokensB.pop();
    filteredRows.forEach(row => row.pop());
    if (filteredCategB.length) {
      filteredCategB.pop();
    }
  }

  const result = {
    tokens_a:    filteredTokensA,
    tokens_b:    filteredTokensB,
    attributions: filteredRows,
    ...extras,
  };

  if (tokens_a_categorized.length) {
    result.tokens_a_categorized = filteredCategA;
  }
  if (tokens_b_categorized.length) {
    result.tokens_b_categorized = filteredCategB;
  }

  return result;
}



export function arraysEqual(a, b) {
  return a.length === b.length && a.every((v, i) => v === b[i])
}

export function are3DArraysEqual(arr1, arr2) {
  if (!Array.isArray(arr1) || !Array.isArray(arr2)) return false;

  if (arr1.length !== arr2.length) return false;

  for (let i = 0; i < arr1.length; i++) {
    const sub1 = arr1[i], sub2 = arr2[i];
    
    if (!Array.isArray(sub1) || !Array.isArray(sub2) || sub1.length !== sub2.length) return false;

    for (let j = 0; j < sub1.length; j++) {
      const row1 = sub1[j], row2 = sub2[j];
      if (!Array.isArray(row1) || !Array.isArray(row2) || row1.length !== row2.length) return false;

      for (let k = 0; k < row1.length; k++) {
        if (row1[k] !== row2[k]) return false;
      }
    }
  }

  return true;
}
