
(cl:in-package :asdf)

(defsystem "path_sender-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :geometry_msgs-msg
)
  :components ((:file "_package")
    (:file "WayPoints" :depends-on ("_package_WayPoints"))
    (:file "_package_WayPoints" :depends-on ("_package"))
  ))