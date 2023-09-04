# ML Duplicate Detection - [inzpo.me](https://inzpo.me)

## 📋 Overview

This repository showcases a snippet from a larger Django project ([inzpo.me](https://inzpo.me)) that uses **Machine Learning** algorithms for the automated analysis and management of potential duplicate content.
<br>

[inzpo.me](https://inzpo.me), a passion project of mine & [Dyaland](https://github.com/Dyaland), is a first-of-its-kind platform that uses Python and Django to seamlessly connect people with inspiring personalities by notifying users of guest appearances on podcasts. The platform emphasizes scalability, performance optimization, and user engagement through various integrations like Spotify/ChatGPT APIs, Django Q2 for async task management, trie search for efficient data retrieval, custom caching mechanisms and other innovative functionalities.
<br>
Using scikit-learn's TF-IDF Vectorization and Cosine Similarity features, this logic efficiently identifies potential duplicate entries in large datasets. The detection process runs daily, comparing only the newly scraped episodes against the existing ones in the PostgreSQL-database, thereby optimizing efficiency.

<br>

To enhance manageability, a custom Django Admin view is also implemented. This allows for easy identification and exclusion of duplicates.

<br>

## 🌟 Features

- **ML-Driven Analysis**: Utilizes Machine Learning algorithms for feature extraction and similarity computation.
- **TF-IDF Vectorization**: Transforms textual data into numerical vectors for advanced analysis.
- **Cosine Similarity**: Computes similarity scores to accurately identify potential duplicates.
- **Custom Django Admin View**: Facilitates the management of potential duplicates, allowing for quick decision-making on whether an entry is a duplicate or not.
- **Optimized Daily Runs**: The duplicate detection process is designed to run daily, focusing only on newly scraped episodes for comparison against the existing database, making it highly efficient.


<br>

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Summary:

1. **Permission**: The software and associated documentation files can be used, copied, modified, merged, published, distributed, sublicensed, and/or sold.
2. **Condition**: Proper attribution must be given to the original author and the MIT license text must be included in all copies or substantial portions of the software.
3. **No Warranty**: The software is provided "as is", without any warranty.

For the full license, please refer to the [LICENSE](LICENSE) file in the repository.

<br>

## 💬 Feedback & Contact

I'd love to network, discuss tech, or swap music recommendations. Feel free to connect with me on:

🌐 **LinkedIn**: [Björn Hödel](https://www.linkedin.com/in/bjornhodel)<br>
🐦 **Twitter**: [@hodel33](https://twitter.com/hodel33)<br>
📸 **Instagram**: [@hodel33](https://www.instagram.com/hodel33)<br>
📧 **Email**: [hodel33@gmail.com](mailto:hodel33@gmail.com)
