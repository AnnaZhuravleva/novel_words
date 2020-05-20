# -*- coding: utf-8 -*-
"""stimuli_preparation.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Oy6CnlVkvtVzj1I8MlaDegmn_OI6wMbH
"""

#  !wget https://rusvectores.org/static/models/ruscorpora_upos_skipgram_300_10_2017.bin.gz
#  !wget http://rusvectores.org/static/models/rusvectores2/ruscorpora_mystem_cbow_300_2_2015.bin.gz
#  from google.colab import files

import gensim
import random
import sklearn
import itertools
import numpy as np
import pandas as pd
from collections import Counter

m_2017 = 'ruscorpora_upos_skipgram_300_10_2017.bin.gz'
model_2017 = gensim.models.KeyedVectors.load_word2vec_format(m_2017, binary=True)
model_2017.init_sims(replace=True)

m_2015 = 'ruscorpora_mystem_cbow_300_2_2015.bin.gz'
model_2015 = gensim.models.KeyedVectors.load_word2vec_format(m_2015, binary=True)
model_2015.init_sims(replace=True)

L1_path = 'srcs/l1.csv'
AL_path = 'srcs/al.csv'


class word2vec:

    def __init__(self, model_15, model_17):
        self.model_15 = model_15
        self.model_17 = model_17

    def get_similarity_matrix(self, words):
        vecs = dict()
        for word in words:
          vecs[word] = {w: self.two_words(word, w) for w in words if w != word}
        return vecs


    def get_scores(self, stimuli_list, save=False):
        all_similarities = {}
        vecs = np.array([self.model_15[word+ '_S'] for word in stimuli_list])
        all_sim = {}
        for idx, word in enumerate(stimuli_list):
            sims = self.model_15.cosine_similarities(vecs[idx], vecs)
            all_sim[word] = sims
            ranged = np.argsort(sims, axis=-1)
            less_sim = [(stimuli_list[i], sims[i]) for i in ranged]
            all_similarities[word] = less_sim[:-1]
        sim_means = dict()
        for word in stimuli_list:
            my_array = np.array([i[1] for i in all_similarities[word]])
            sim_means[word] = (np.mean(my_array), max(my_array), np.std(my_array))
        all_scores = pd.DataFrame(stimuli_list, columns=['keys']).join(
                    pd.DataFrame(all_sim))

        for word in all_similarities:
          all_similarities[word] = sorted(all_similarities[word], 
                                          key=lambda x: x[1], reverse=True)
        if save:
            all_scores.to_excel('sim_scores_all.xlsx')
            #  files.download('sim_scores_all.xlsx')
        return sim_means, all_similarities

    def two_words(self, w1, w2):
      return self.model_17.similarity( f'{w1}_NOUN', f'{w2}_NOUN')


class L1:

    def __init__(self, model, L1_path):
      self.model = model
      self.l1_path = L1_path


    def get_l1_list(self, file='L1_candidates.csv', save=False, 
                    top_sim=0.47):
        candidates = pd.read_csv(file, sep=';')
        words = candidates['dominant_name']
        _, scores = self.model.get_scores(words)
        all_s = {}
        for word in scores:
            all_s[word] = [x for x in scores[word] if x[1] > top_sim]
        raw = [x for x in all_s if all_s[x] == []]
        rich = [(x, all_s[x]) for x in all_s if all_s[x] != []]
        rich_set = []
        my_set = []
        for word in rich:
          rich_set += [x[0] for x in word[1]]
          if word[0] not in rich_set:
            my_set.append(word[0])

        _, scores  = self.model.get_scores(raw + my_set)
        all_s = {}
        for word in scores:
            all_s[word] = [x for x in scores[word] if x[1] > top_sim]
        raw_2 = [x for x in all_s if all_s[x] == []]

        e, _ = self.model.get_scores(raw_2)

        my_table = pd.DataFrame([(x, e[x][0], e[x][1], e[x][2]) for x in e], 
                                columns=['dominant_name', 'sim_score_mean', 
                                        'sim_score_max', 'sim_score_sd'])
        all_stim = pd.merge(candidates, my_table, on='dominant_name', how='right')
        if save:
          all_stim.to_excel('all_data.xlsx', index=False)
          #  files.download('all_data.xlsx')
        return all_stim

    def divide_l1(self, offset=2):
        mini_dict = {'самолет':'руль',
                    'руль':'самолет',
                    'корона':'костюм',
                    'костюм':'корона'}
        df = pd.read_csv(self.l1_path, sep=';')
        words = [i.dominant_name for _, i in df.iterrows()]
        vecs = self.model.get_similarity_matrix(words)
        set_1 = []
        set_2 = []
        all_sets = list(vecs.keys())
        for i in range(40):
            random.seed(i*offset)
            word = random.choice(all_sets)
            most_sim = sorted(vecs[word].items(), 
                              key=lambda x: x[1], reverse=True)
            most_sim = [i for i in most_sim if i[0] in all_sets and i[0] != word]
            try:
              most_sim = most_sim[0][0]
              if (most_sim in list(mini_dict.keys()) \
                  and mini_dict[most_sim] in set_2) or \
                  (word in list(mini_dict.keys()) \
                  and mini_dict[word] in set_1):
                  most_sim, word = word, most_sim
              set_1.append(word)
              set_2.append(most_sim)
              all_sets.remove(word)
              all_sets.remove(most_sim)
            except Exception as e:
              print(e, most_sim, word)                
        return list(sorted(set_1)), list(sorted(set_2))

    def l1_stats(self, set_1, set_2, save=False):
        with open(self.l1_path, 'r') as f:
          l1_all = pd.read_csv(f, sep=';') 

        for idx, item in enumerate([set_1, set_2]):
            df = pd.DataFrame(item, columns =['dominant_name'])
            tmp = pd.merge(l1_all, df, on=['dominant_name'])
            sims = dict()
            matrix = self.model.get_similarity_matrix(item)
            for word in item:
                sims[word] = np.mean(matrix[item])
            tmp['sim_score_mean'] = list(scores.values())
            for param in ['Frequency', 'Phonemes',
                          'Imageability_Mean', 
                          'Age_acquisition_Mean',
                          'Object_familiarity_Mean']:
                tmp[param] = [float(str(i).replace(',', '.')) for i in tmp[param]]
            print(tmp.mean(), '\n=============\n')

            if save:
                tmp.to_excel(f'l1_set_{idx+1}.xlsx', index=False)
                #  files.download(f'l1_set_{idx+1}.xlsx')


class AFC_task:

    def __init__(self, model, L1_path):
        self.model = model
        self.l1_path = L1_path

    def getafc(self, word_set, max_nb=4):
        two = list(iter(itertools.combinations(word_set, 2)))
        used = list()
        my_counter = Counter()
        for idx, word in enumerate(word_set):
            array = [i for i in two 
                    if word in i 
                    and i not in used 
                    and my_counter[i[0]] <= max_nb
                    and my_counter[i[1]] <= max_nb
                    and self.model.two_words(i[0], i[1]) < 0.3
                    ]
            random.seed(idx)
            t = random.choice(array)
            my_counter[t[0]] += 1
            my_counter[t[1]] += 1
            used.append(t)

        wordset = word_set[:]
        pairs = [sorted(tuple(i)) for i in used]
        res = dict()
        for pair in pairs:
          head = {word: (self.model.two_words(word, pair[0]),
                        self.model.two_words(word, pair[1]))
                  for word in wordset}
          tmp_head = {word: head[word] for word in head
                  if head[word][0] < 0.3 and head[word][1] < 0.3
                  and sorted(tuple([pair[0], word])) not in pairs
                  and sorted(tuple([pair[1], word])) not in pairs}
          if len(tmp_head) == 0:
            tmp_head = {word: head[word] for word in head
                  if sorted(tuple([pair[0], word])) not in pairs
                  and sorted(tuple([pair[1], word])) not in pairs}
          head = sorted(tmp_head.items(), key = lambda x: np.sum(x[1]))[0][0]
          res[head] = pair
          wordset.remove(head)
        return res


    def __call__(self, set_1, set_2, save=False):
        a = self.getafc(set_1)
        b = self.getafc(set_2)
        a['стрела'][0], a['колокол'][0] = a['колокол'][0], a['стрела'][0]
        a['ведро'], a['колокол'] = a['колокол'], a['ведро']
        
        with open(self.l1_path, 'r') as f:
            df = pd.read_csv(f, sep=';')

        if save: 
            for idx, word_set in enumerate([a, b]):
              set1 = []
              for word in word_set:
                set1.append([
                            word, a[word][0], a[word][1], 
                            self.model.two_words(word, a[word][0]),
                            self.model.two_words(word, a[word][1]),
                            self.model.two_words(a[word][0], a[word][1])
                            ])

              set1 = pd.DataFrame(set1, columns=['dominant_name',
                                                'AFC1', 'AFC2',
                                                'chosen_distance_word_to_1', 
                                                'chosen_distance_word_to_2',
                                                'chosen_distance_1_to_2'])
          
              set1 = pd.merge(set1, df, on=['dominant_name'])
              set1.to_excel(f'afc{idx+1}.xlsx', index=False)
              #  files.download(f'afc{idx+1}.xlsx')
              self.afc_stats([a, b])

        return a, b

    @staticmethod
    def afc_stats(afc):
      tables = []
      for idx in [0, 1]:
          one = Counter()
          two = Counter()

          for word in afc[idx]:
            one[afc[idx][word][0]] += 1
            one[afc[idx][word][1]] += 1
            two[tuple([word, afc[idx][word][1]])] += 1
            two[tuple([word, afc[idx][word][0]])] += 1
            two[tuple(afc[idx][word])] += 1

          A = pd.DataFrame([[i, one[i]] for i in one]) 
          B = pd.DataFrame([[f'{i[0]} {i[1]}', two[i]] for i in two])
          C = pd.concat([A, B], axis=0, join='outer')
          tables.append(C)
      D = pd.concat(tables, axis=1, join='outer')
      D.to_excel('afc_stats.xlsx',index=False)
      #  files.download('afc_stats.xlsx')
      return D


class recognition:

    def __call__(self, word_list, al, nbs, offset=15):
        words = word_list[:]
        r_keys = dict()
        for i in range(20):
            random.seed(i*offset)
            word = random.choice(words)
            r_keys[word] = word
            words.remove(word)
        distractors = words[:]

        for idx, word in enumerate(words):
            random.seed((idx+20)*offset)
            k = random.choice(distractors)
            r_keys[word] = k
            distractors.remove(k)
        recog_list = {w: r_keys[w] for w in word_list}
        recog_cor = [int(recog_list[s] == s) for s in recog_list]
        recog_list = [f'{s} = {recog_list[w]}?' for w, s in zip(recog_list, al)]
        return recog_list, recog_cor


class AL:

    def __init__(self, file):
        self.file = file
        self.pw = list(self.create_pw())

    def __call__(self):
        return self.pw
    
    def create_pw(self, offset=3, save=False):
        with open(self.file, 'r') as f:
            words = pd.read_csv(f, sep=';')[:80]
        set_1 = []
        set_2 = []
        u = [item for item in words['word'] if item[-1] == 'u']
        e = [item for item in words['word'] if item[-1] == 'e']
        for idx in range(40):
          random.seed(idx*offset)
          wu = random.choice(u)
          we = random.choice(e)
          if idx % 2 == 0:
            set_1 += [wu, we]
          else:
            set_2 += [wu, we]
          u.remove(wu)
          e.remove(we)

        for idx, al in enumerate([set_1, set_2]):  
          al = pd.merge(words, pd.DataFrame(al, columns=['word']), on=['word'])
          for param in ['mean_dist', 'mean_valency', 'sd_valency']:
              al[param] = [float(i.replace(',', '.')) for i in al[param]]
          if save:
            al.to_excel(f'al{idx+1}.xlsx')
            #  files.download(f'al{idx+1}.xlsx')
          
          yield al['word']


class Experiment:

    def __init__(self, m15, m17, L1_path, AL_path):
      self.w2v = word2vec(m15, m17)
      self.L1 = L1(self.w2v, L1_path)
      self.AL = AL(AL_path)
      self.AFC = AFC_task(self.w2v, L1_path)
      self.recog = recognition()


    @staticmethod
    def random_numbers(save=False):
        """
        generates a unique L1 order for each experimental list
        """
        all_sets = []
        idx = 0
        a = list(range(40))
        while len(all_sets) < 200:
          tmp = list()
          while len(tmp) < 40:
            idx += 1
            random.seed(idx)
            q = random.choice(a)
            if q not in tmp:
              tmp.append(q)
          if tmp not in all_sets:
            all_sets.append(tmp)
        prev = []
        for idx, item in enumerate(all_sets[:]):
          if item[:4] in prev:
            all_sets.remove(item)
          else:
            prev.append(item[:4])
        if save:
            pd.DataFrame(all_sets).to_excel('numbers.xlsx', index=False)
            #  files.download('numbers.xlsx')
        return all_sets

    def single_list(self, nbs, word_set, al, afc_dict, i):
        s1 = [word_set[idx] for idx in nbs]
        sound_paths = [f'{word}.wav' for word in al]
        afc = []
        for idx in range(40):
          word = s1[idx]
          random.seed(idx*15)
          w = random.sample([word, afc_dict[word][0], afc_dict[word][1]], 3)
          afc.append(w)
        afc0 = [w[0] for w in afc]
        afc1 = [w[1] for w in afc]
        afc2 = [w[2] for w in afc]
        afc0_color = [('black', 'green')[w[0] == s] for w, s in zip(afc, s1)]
        afc1_color = [('black', 'green')[w[1] == s] for w, s in zip(afc, s1)]
        afc2_color = [('black', 'green')[w[2] == s] for w, s in zip(afc, s1)]
        recog_list, recog_cor = self.recog(s1, al, nbs, offset=i)
        recall_al = [al[nb] for nb in nbs]
        recall_l1 = [s1[nb] for nb in nbs]
        sem_al = [recall_al[nb] for nb in nbs]
        table = list(zip(
            al, s1, sound_paths, 
            afc0, afc1, afc2, 
            afc0_color, afc1_color, afc2_color,
            recog_list, recog_cor,  
            recall_al, recall_l1,
            sem_al
            ))
        table = [table[idx] for idx in nbs]
        df = pd.DataFrame(table,
            columns = [
                      'AL', 'L1', 'sound_path', 
                      'AFC1', 'AFC2', 'AFC3',
                      'AFC1_color', 'AFC2_color', 'AFC3_color',
                      'recognition_text', 'recognition_correctness',
                      'recall_AL', 'recall_L1',
                      'SEM_AL'
            ])
        return df


    def get_all(self, save=False, list_nb=15):
        al = self.AL()

        set_1, set_2 = self.L1.divide_l1(offset=1)
        afc_1, afc_2 = self.AFC(set_1, set_2)

        numbers = self.random_numbers()
        for i in range(list_nb):
          df_1 = self.single_list(numbers[i], set_1, al[i % 2 == 1], afc_1, i)
          df_2 = self.single_list(numbers[i], set_2, al[i % 2 == 0], afc_2, i)
          if save:
              df_1.to_excel(f'session_1_{i}.xlsx', index=False)
              df_2.to_excel(f'session_2_{i}.xlsx', index=False)
              #  files.download(f'session_1_{i}.xlsx')
              #  files.download(f'session_2_{i}.xlsx') 
          yield df_1, df_2


if __name__ == '__main__':
    exp = Experiment(model_2015, model_2017, L1_path, AL_path)
    res = list(exp.get_all())
