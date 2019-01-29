import os
import numpy as np
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from speechrecognition.dataset.dataset_base import DatasetBase
from speechrecognition.utils import audio_utils, text_utils


class VCTKDataset(DatasetBase):
    """" VCTKDataset process data from VCTK Corpus
    Args:
        dataset_path
        num_features
        num_context
    """


    def __init__(self, dataset_path, num_speakers, num_features, num_context):
        DatasetBase.__init__(self, num_features, num_context)

        self.dataset_path = dataset_path

        self._train_audios = []
        self._train_labels = []
        self._test_audios = []
        self._test_labels = []

        self.read_dataset(dataset_path, num_speakers)

    def read_dataset(self, dataset_path=None, num_speakers=None):

        audio_filenames, label_filenames = self.get_dataset_filenames(dataset_path, num_speakers)

        audios = []
        labels = []
        num_examples = len(audio_filenames)

        t_files = tqdm(zip(audio_filenames, label_filenames), total=num_examples, desc='Preprocessing VCTK Dataset')
        for audio_filename, label_filename in t_files:

            # Progress bar info
            t_audio_file = '/'.join(audio_filename.split('/')[-4:])
            t_label_file = '/'.join(label_filename.split('/')[-4:])
            t_files.set_postfix(audio_file=f'{t_audio_file}', label_file=f'{t_label_file }')

            audio_features = audio_utils.audiofile_to_input_vector(audio_filename, self.num_features, self.num_context)
            text_target = text_utils.get_refactored_transcript(label_filename, is_filename=True, is_digit=False)

            audios.append(audio_features)
            labels.append(text_target)

        audios = np.asarray(audios)
        labels = np.asarray(labels)

        # preshuffle dataset (the main shuffle will be performed in tf.dataset)
        self.shuffle(audios, labels, seed=42)

        # split dataset to train and test
        train_x, test_x, train_y, test_y = train_test_split(audios, labels, test_size=0.3, random_state=42)
        self._train_audios = train_x
        self._train_labels = train_y
        self._test_audios = test_x
        self._test_labels = test_y


    def get_dataset_filenames(self, dataset_path=None, num_speakers=None):
        """" Retrives filenames from VCTK structues corpus and stores them in VCTKDataset object
        Args:
            dataset_path (string) - given path to home directory of dataset
        """

        if dataset_path is not None:
            self.dataset_path = dataset_path

        print("Retriving all filenames for VCTK training dataset from path", self.dataset_path)

        audio_dataset_path = os.path.join(self.dataset_path, 'wav48')
        label_dataset_path = os.path.join(self.dataset_path, 'txt')

        # gets list of directories for diffrent speakers
        speakers_dirs = os.listdir(audio_dataset_path)

        if num_speakers is not None:
            speakers_dirs = speakers_dirs[0:num_speakers]
            print('Number of speakers: ', num_speakers)
        else:
            print('All speakers')

        audio_filenames = []
        label_filenames = []

        for speaker_dir in speakers_dirs:
            # get full paths for speakers
            speaker_audio_path = os.path.join(audio_dataset_path, speaker_dir)
            speaker_label_path = os.path.join(label_dataset_path, speaker_dir)

            # ignore inconsistency in data or anything that is not directory
            if not os.path.isdir(speaker_audio_path) or not os.path.isdir(speaker_label_path):
                continue

            # Getting full paths to all audios and labels of the speaker
            audio_paths = [os.path.join(speaker_audio_path, speaker_filename) for speaker_filename in
                           os.listdir(speaker_audio_path)]
            label_paths = [os.path.join(speaker_label_path, speaker_filename) for speaker_filename in
                           os.listdir(speaker_label_path)]

            audio_paths.sort()
            label_paths.sort()

            # concatenate speaker filenames
            audio_filenames = audio_filenames + audio_paths
            label_filenames = label_filenames + label_paths

        return audio_filenames, label_filenames


def test_dataset():

    dataset_path = '/Users/adamzvada/Documents/School/BP/VCTK-Corpus'

    vctk_dataset = VCTKDataset(dataset_path=dataset_path, num_speakers=1, num_features=13, num_context=4)

    #vctk_dataset.save_pickle_dataset('test')
    train_input, sparse_targets, train_length = vctk_dataset.next_batch(8)

    print(train_input)
    print(sparse_targets)
    print(train_length)

if __name__ == "__main__":

    test_dataset()