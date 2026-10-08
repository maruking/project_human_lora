# STEP6 Reference Audit

Identity-only audit. Historical threshold is not a measured FAR/FRR guarantee. No quality ranking, quotas or final training selection.

identity_state is authoritative. identity_passed is a compatibility field only. Duplicate members are not identity rejects.

[Source-linked review](STEP6_REFERENCE_REVIEW.html)

```json
{
  "reference_audit_status": "PASS",
  "total_references": 7,
  "valid_references": 7,
  "invalid_references": 0,
  "reference_outliers": 0,
  "embedding_dim": 512,
  "historical_identity_threshold": 0.55,
  "min_reference_count": 3,
  "max_reference_count": 20,
  "reference_confirmation": "User places explicitly confirmed identity anchors in configured reference directory; not automatically selected",
  "backend": "insightface",
  "model": "buffalo_l",
  "insightface_version": "0.7.3",
  "onnxruntime_version": "1.23.2",
  "device": "cuda",
  "providers": {
    "detection": [
      "CUDAExecutionProvider",
      "CPUExecutionProvider"
    ],
    "recognition": [
      "CUDAExecutionProvider",
      "CPUExecutionProvider"
    ]
  },
  "model_sha256": {
    "1k3d68.onnx": "df5c06b8a0c12e422b2ed8947b8869faa4105387f199c477af038aa01f9a45cc",
    "2d106det.onnx": "f001b856447c413801ef5c42091ed0cd516fcd21f2d6b79635b1e733a7109dbf",
    "det_10g.onnx": "5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91",
    "genderage.onnx": "4fde69b1c810857b88c64a335084f1c3fe8f01246c9a191b48c7bb756d6652fb",
    "w600k_r50.onnx": "4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43"
  },
  "preprocessing": "InsightFace original-image detection, five-point alignment, recognition model defaults",
  "detection_input_size": [
    640,
    640
  ],
  "detection_threshold": 0.5,
  "leave_one_out_distribution": {
    "count": 7,
    "min": 0.6627492630157726,
    "P05": 0.6676921252659554,
    "P10": 0.6726349875161383,
    "median": 0.6990476401122694,
    "P90": 0.739039864527928,
    "max": 0.7623835238044114
  },
  "step6_version": "step6_identity_v2",
  "reference_directory_sha256": "2a1c29863aed24b4a4e63df9fc4d45ea9c1a8c41a0bb5cbdedac447b40515bd2"
}
```
