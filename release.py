import os
import sys
import shutil

def copy_file(source, target):
    # adding exception handling
    try:
        print(f"copy file {source} -> {target}")
        shutil.copy(source, target)
    except IOError as e:
        print("Unable to copy file. %s" % e)
    except:
        print("Unexpected error:", sys.exc_info())

def release_docker_images(images,dst_path):
    pass
    

def release_code(code_path,dst_path):
    pass
    


if __name__ == "__main__":
    #从终端读取版本号
    version = input("version:")
    
    cur_path = os.path.dirname(os.path.abspath(__file__))
    release_path = os.path.join(cur_path,f"release/cluster-health-v{version}")
    
    print("release path:",release_path)
    
    if os.path.exists(release_path): 
        print("release path exists,remove it")
        os.removedirs(release_path)
    print("create release path,",release_path)
    os.makedirs(release_path)
    
    #cp install.sh
    copy_file(os.path.join(cur_path,'script/install.sh'),release_path)
    
    #cp images
    release_docker_images(os.path.join(release_path,'images'),release_path)
    
    #cp code
    release_code(os.path.join(cur_path,'code'),release_path)
    
    print("release done")
    